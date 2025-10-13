package main

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	// Controllers - OCR
	processimage "github.com/plobin/genkitgo/internal/http/controllers/OCR/ProcessImage"
	processpdf "github.com/plobin/genkitgo/internal/http/controllers/OCR/ProcessPDF"

	// Controllers - Analysis
	analyzedocument "github.com/plobin/genkitgo/internal/http/controllers/Analysis/AnalyzeDocument"

	// Controllers - Blocks
	getblock "github.com/plobin/genkitgo/internal/http/controllers/Blocks/GetBlock"
	updateblock "github.com/plobin/genkitgo/internal/http/controllers/Blocks/UpdateBlock"
	deleteblock "github.com/plobin/genkitgo/internal/http/controllers/Blocks/DeleteBlock"

	// Controllers - Pages
	listpages "github.com/plobin/genkitgo/internal/http/controllers/Pages/ListPages"
	getpage "github.com/plobin/genkitgo/internal/http/controllers/Pages/GetPage"

	// Controllers - Images
	getimage "github.com/plobin/genkitgo/internal/http/controllers/Images/GetImage"

	// Controllers - Requests
	listrequests "github.com/plobin/genkitgo/internal/http/controllers/Requests/ListRequests"
	getrequest "github.com/plobin/genkitgo/internal/http/controllers/Requests/GetRequest"
	createrequest "github.com/plobin/genkitgo/internal/http/controllers/Requests/CreateRequest"

	// Controllers - Meta
	serverstatus "github.com/plobin/genkitgo/internal/http/controllers/Meta/ServerStatus"
)

func main() {
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))

	// CORS 설정
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	})

	// Health check
	r.Get("/", serverstatus.Handle)

	// API Routes - OCR 도메인
	r.Post("/api/ocr/process-image", processimage.Handle)
	r.Post("/api/ocr/process-pdf", processpdf.Handle)

	// API Routes - Analysis 도메인
	r.Post("/api/analysis/analyze-document", analyzedocument.Handle)

	// API Routes - Blocks 도메인
	r.Get("/api/blocks", getblock.Handle)
	r.Put("/api/blocks", updateblock.Handle)
	r.Delete("/api/blocks", deleteblock.Handle)

	// API Routes - Pages 도메인
	r.Get("/api/pages", listpages.Handle)
	r.Get("/api/pages/detail", getpage.Handle)

	// API Routes - Images 도메인
	r.Get("/api/images", getimage.Handle)

	// API Routes - Requests 도메인
	r.Get("/api/requests", listrequests.Handle)
	r.Get("/api/requests/detail", getrequest.Handle)
	r.Post("/api/requests", createrequest.Handle)

	// 서버 시작
	port := ":6003"
	log.Printf("🚀 GenkitGo OCR API 서버 시작: http://localhost%s\n", port)
	log.Printf("📚 API 문서: http://localhost%s/docs\n", port)

	if err := http.ListenAndServe(port, r); err != nil {
		log.Fatalf("서버 시작 실패: %v", err)
	}
}
