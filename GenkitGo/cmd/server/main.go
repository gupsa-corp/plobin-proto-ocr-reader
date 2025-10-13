package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/plobin/genkitgo/internal/config"
	"github.com/plobin/genkitgo/internal/models"
	"github.com/plobin/genkitgo/internal/services/Block/DeleteBlock"
	"github.com/plobin/genkitgo/internal/services/Block/GetBlock"
	"github.com/plobin/genkitgo/internal/services/Block/UpdateBlock"
	"github.com/plobin/genkitgo/internal/services/File/Storage"
	"github.com/plobin/genkitgo/internal/services/Image/GetImage"
	"github.com/plobin/genkitgo/internal/services/LLM/Client"
	"github.com/plobin/genkitgo/internal/services/OCR/ExtractBlocks"
	"github.com/plobin/genkitgo/internal/services/PDF/ProcessPDF"
	"github.com/plobin/genkitgo/internal/services/Page/GetPage"
	"github.com/plobin/genkitgo/internal/services/Page/ListPages"
	"github.com/plobin/genkitgo/internal/services/Template/CreateTemplate"
	"github.com/plobin/genkitgo/internal/services/Template/DeleteTemplate"
	"github.com/plobin/genkitgo/internal/services/Template/GetTemplate"
	"github.com/plobin/genkitgo/internal/services/Template/ListTemplates"
)

func main() {
	// Load configuration
	cfg := config.Load()
	
	// Initialize services
	llmClient := Client.NewLLMClient(cfg.LLMBaseURL, cfg.LLMAPIKey, cfg.LLMModel)
	defer llmClient.Close()

	// Initialize OCR and PDF services (Pure Go - No Python dependency!)
	ocrService := ExtractBlocks.NewService(cfg.OCRLanguage)
	pdfService := ProcessPDF.NewService(cfg.OCRLanguage, 150.0)
	storageService := Storage.NewService(cfg.OutputDir)

	// Block services
	getBlockService := GetBlock.NewService(cfg.OutputDir)
	updateBlockService := UpdateBlock.NewService(cfg.OutputDir)
	deleteBlockService := DeleteBlock.NewService(cfg.OutputDir)

	// Page services
	getPageService := GetPage.NewService(cfg.OutputDir)
	listPagesService := ListPages.NewService(cfg.OutputDir)

	// Image service
	getImageService := GetImage.NewService(cfg.OutputDir)

	// Template services
	listTemplatesService := ListTemplates.NewService(cfg.OutputDir)
	createTemplateService := CreateTemplate.NewService(cfg.OutputDir)
	getTemplateService := GetTemplate.NewService(cfg.OutputDir)
	deleteTemplateService := DeleteTemplate.NewService(cfg.OutputDir)

	log.Printf("✅ Services initialized (Pure Go - No Python!)")
	log.Printf("  - LLM Client (model: %s)", cfg.LLMModel)
	log.Printf("  - OCR Service (Tesseract via gosseract)")
	log.Printf("  - PDF Service (MuPDF via go-fitz)")
	log.Printf("  - Storage Service (dir: %s)", cfg.OutputDir)
	log.Printf("  - Block Services (Get, Update, Delete)")
	log.Printf("  - Page Services (Get, List)")
	log.Printf("  - Image Service (Get)")
	log.Printf("  - Template Services (List, Create, Get, Delete)")
	
	// Create router
	r := chi.NewRouter()
	
	// Middleware
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))
	
	// Health check
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status": "ok", "message": "Genkit OCR API is running"}`)
	})
	
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status": "healthy"}`)
	})
	
	// API routes
	r.Route("/api", func(r chi.Router) {
		// OCR endpoints
		r.Post("/process-image", func(w http.ResponseWriter, r *http.Request) {
			// Parse multipart form
			if err := r.ParseMultipartForm(32 << 20); err != nil { // 32MB max
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to parse form",
					Error:   err.Error(),
				})
				return
			}

			file, header, err := r.FormFile("file")
			if err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "No file provided",
					Error:   err.Error(),
				})
				return
			}
			defer file.Close()

			// Save temporary file
			tmpFile, err := os.CreateTemp("", "upload-*.png")
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to create temporary file",
					Error:   err.Error(),
				})
				return
			}
			defer os.Remove(tmpFile.Name())
			defer tmpFile.Close()

			if _, err := io.Copy(tmpFile, file); err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to save file",
					Error:   err.Error(),
				})
				return
			}

			// Process with OCR
			options := models.OCROptions{
				MergeBlocks:    true,
				MergeThreshold: 30,
				Language:       cfg.OCRLanguage,
			}

			result, err := ocrService.Execute(r.Context(), tmpFile.Name(), options)
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "OCR processing failed",
					Error:   err.Error(),
				})
				return
			}

			// Create request in storage
			requestID, err := storageService.CreateRequest(header.Filename, models.RequestTypeImage, header.Size, 1)
			if err != nil {
				log.Printf("Warning: Failed to create request storage: %v", err)
			} else {
				result.RequestID = requestID
			}

			// Return success response
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.ProcessImageResponse{
				Success: true,
				Message: "Image processed successfully",
				Data:    result,
			})
		})

		// PDF processing endpoint
		r.Post("/process-pdf", func(w http.ResponseWriter, r *http.Request) {
			if err := r.ParseMultipartForm(32 << 20); err != nil {
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to parse form",
					Error:   err.Error(),
				})
				return
			}

			file, header, err := r.FormFile("file")
			if err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "No file provided",
					Error:   err.Error(),
				})
				return
			}
			defer file.Close()

			tmpFile, err := os.CreateTemp("", "upload-*.pdf")
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to create temporary file",
					Error:   err.Error(),
				})
				return
			}
			defer os.Remove(tmpFile.Name())
			defer tmpFile.Close()

			if _, err := io.Copy(tmpFile, file); err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to save file",
					Error:   err.Error(),
				})
				return
			}

			options := models.OCROptions{
				MergeBlocks:    true,
				MergeThreshold: 30,
				Language:       cfg.OCRLanguage,
			}

			result, err := pdfService.Execute(r.Context(), tmpFile.Name(), options)
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "PDF processing failed",
					Error:   err.Error(),
				})
				return
			}

			requestID, err := storageService.CreateRequest(header.Filename, models.RequestTypePDF, header.Size, result.TotalPages)
			if err != nil {
				log.Printf("Warning: Failed to create request storage: %v", err)
			} else {
				result.RequestID = requestID
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "PDF processed successfully",
				Data:    result,
			})
		})

		// Analysis endpoint
		r.Post("/analyze", func(w http.ResponseWriter, r *http.Request) {
			var req struct {
				Text   string `json:"text"`
				Prompt string `json:"prompt"`
			}

			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid request body",
					Error:   err.Error(),
				})
				return
			}

			// Analyze with LLM
			analysis, err := llmClient.AnalyzeText(r.Context(), req.Text, req.Prompt, 0.1)
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "LLM analysis failed",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.AnalyzeResponse{
				Success:  true,
				Message:  "Analysis completed",
				Analysis: analysis,
			})
		})

		// Request management
		r.Get("/requests", func(w http.ResponseWriter, r *http.Request) {
			requests, err := storageService.ListRequests()
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to list requests",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Requests retrieved",
				Data:    requests,
			})
		})

		r.Get("/requests/{id}", func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "id")

			metadata, err := storageService.GetMetadata(id)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Request not found",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Request metadata retrieved",
				Data:    metadata,
			})
		})

		// Block endpoints
		r.Get("/blocks/{request_id}/{block_id}", func(w http.ResponseWriter, r *http.Request) {
			requestID := chi.URLParam(r, "request_id")
			blockIDStr := chi.URLParam(r, "block_id")

			var blockID int
			if _, err := fmt.Sscanf(blockIDStr, "%d", &blockID); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid block ID",
					Error:   err.Error(),
				})
				return
			}

			block, err := getBlockService.Execute(r.Context(), requestID, blockID)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Block not found",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Block retrieved",
				Data:    block,
			})
		})

		r.Put("/blocks/{request_id}/{block_id}", func(w http.ResponseWriter, r *http.Request) {
			requestID := chi.URLParam(r, "request_id")
			blockIDStr := chi.URLParam(r, "block_id")

			var blockID int
			if _, err := fmt.Sscanf(blockIDStr, "%d", &blockID); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid block ID",
					Error:   err.Error(),
				})
				return
			}

			var req struct {
				Text string `json:"text"`
			}
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid request body",
					Error:   err.Error(),
				})
				return
			}

			block, err := updateBlockService.Execute(r.Context(), requestID, blockID, req.Text)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to update block",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Block updated",
				Data:    block,
			})
		})

		r.Delete("/blocks/{request_id}/{block_id}", func(w http.ResponseWriter, r *http.Request) {
			requestID := chi.URLParam(r, "request_id")
			blockIDStr := chi.URLParam(r, "block_id")

			var blockID int
			if _, err := fmt.Sscanf(blockIDStr, "%d", &blockID); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid block ID",
					Error:   err.Error(),
				})
				return
			}

			if err := deleteBlockService.Execute(r.Context(), requestID, blockID); err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to delete block",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Block deleted",
				Data:    nil,
			})
		})

		// Page endpoints
		r.Get("/pages/{request_id}/{page_number}", func(w http.ResponseWriter, r *http.Request) {
			requestID := chi.URLParam(r, "request_id")
			pageNumStr := chi.URLParam(r, "page_number")

			var pageNumber int
			if _, err := fmt.Sscanf(pageNumStr, "%d", &pageNumber); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid page number",
					Error:   err.Error(),
				})
				return
			}

			page, err := getPageService.Execute(r.Context(), requestID, pageNumber)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Page not found",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Page retrieved",
				Data:    page,
			})
		})

		r.Get("/pages/{request_id}", func(w http.ResponseWriter, r *http.Request) {
			requestID := chi.URLParam(r, "request_id")

			pages, err := listPagesService.Execute(r.Context(), requestID)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to list pages",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Pages listed",
				Data:    pages,
			})
		})

		// Image endpoint
		r.Get("/images/{request_id}/{page_number}", func(w http.ResponseWriter, r *http.Request) {
			requestID := chi.URLParam(r, "request_id")
			pageNumStr := chi.URLParam(r, "page_number")

			var pageNumber int
			if _, err := fmt.Sscanf(pageNumStr, "%d", &pageNumber); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid page number",
					Error:   err.Error(),
				})
				return
			}

			image, err := getImageService.Execute(r.Context(), requestID, pageNumber)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Image not found",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", image.ContentType)
			w.Write(image.Data)
		})

		// Template endpoints
		r.Get("/templates", func(w http.ResponseWriter, r *http.Request) {
			templates, err := listTemplatesService.Execute(r.Context())
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to list templates",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Templates listed",
				Data:    templates,
			})
		})

		r.Post("/templates", func(w http.ResponseWriter, r *http.Request) {
			var req models.TemplateCreateRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Invalid request body",
					Error:   err.Error(),
				})
				return
			}

			template, err := createTemplateService.Execute(r.Context(), req)
			if err != nil {
				w.WriteHeader(http.StatusBadRequest)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to create template",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusCreated)
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Template created",
				Data:    template,
			})
		})

		r.Get("/templates/{id}", func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "id")

			template, err := getTemplateService.Execute(r.Context(), id)
			if err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Template not found",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Template retrieved",
				Data:    template,
			})
		})

		r.Delete("/templates/{id}", func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "id")

			if err := deleteTemplateService.Execute(r.Context(), id); err != nil {
				w.WriteHeader(http.StatusNotFound)
				json.NewEncoder(w).Encode(models.ErrorResponse{
					Success: false,
					Message: "Failed to delete template",
					Error:   err.Error(),
				})
				return
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(models.APIResponse{
				Success: true,
				Message: "Template deleted",
				Data:    nil,
			})
		})
	})
	
	// Create server
	srv := &http.Server{
		Addr:         cfg.GetAddress(),
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}
	
	// Start server in goroutine
	go func() {
		log.Printf("Starting server on %s", cfg.GetAddress())
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()
	
	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	log.Println("Shutting down server...")
	
	// Graceful shutdown
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}
	
	log.Println("Server stopped")
}
