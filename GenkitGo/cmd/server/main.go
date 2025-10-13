package main

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	// Controllers
	processimage "github.com/plobin/genkitgo/internal/http/controllers/OCR/ProcessImage"
	processpdf "github.com/plobin/genkitgo/internal/http/controllers/OCR/ProcessPDF"
	analyzedocument "github.com/plobin/genkitgo/internal/http/controllers/Analysis/AnalyzeDocument"
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
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"status":"ok","message":"GenkitGo OCR API Server"}`)
	})

	// API Routes - OCR 도메인
	r.Post("/api/ocr/process-image", processimage.Handle)
	r.Post("/api/ocr/process-pdf", processpdf.Handle)

	// API Routes - Analysis 도메인
	r.Post("/api/analysis/analyze-document", analyzedocument.Handle)

	// 서버 시작
	port := ":6003"
	log.Printf("🚀 GenkitGo OCR API 서버 시작: http://localhost%s\n", port)
	log.Printf("📚 API 문서: http://localhost%s/docs\n", port)

	if err := http.ListenAndServe(port, r); err != nil {
		log.Fatalf("서버 시작 실패: %v", err)
	}
}
