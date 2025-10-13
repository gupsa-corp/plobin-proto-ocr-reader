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
	"github.com/plobin/genkitgo/internal/services/File/Storage"
	"github.com/plobin/genkitgo/internal/services/LLM/Client"
	"github.com/plobin/genkitgo/internal/services/OCR/ExtractBlocks"
)

func main() {
	// Load configuration
	cfg := config.Load()
	
	// Initialize services
	llmClient := Client.NewLLMClient(cfg.LLMBaseURL, cfg.LLMAPIKey, cfg.LLMModel)
	defer llmClient.Close()

	ocrService := ExtractBlocks.NewService("python3", "../FastApi/services/ocr_wrapper.py")
	storageService := Storage.NewService(cfg.OutputDir)

	log.Printf("✅ Services initialized")
	log.Printf("  - LLM Client (model: %s)", cfg.LLMModel)
	log.Printf("  - OCR Service (Surya OCR)")
	log.Printf("  - Storage Service (dir: %s)", cfg.OutputDir)
	
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
