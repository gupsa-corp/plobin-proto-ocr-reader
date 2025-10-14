package config

import (
	"fmt"
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	// Server configuration
	ServerPort string
	ServerHost string
	
	// OCR configuration
	OCREngine   string // "surya" (ML-based layout detection + OCR)
	OCRLanguage string // "kor", "eng", etc.
	UseGPU      bool
	
	// PDF configuration
	PDFDpi int
	
	// LLM configuration
	LLMBaseURL string
	LLMAPIKey  string
	LLMModel   string
	
	// Storage configuration
	OutputDir    string
	CacheDir     string
	TemplateDir  string
	DemoDir      string
	
	// Performance configuration
	MaxWorkers        int
	EnableCompression bool
	
	// Debugging
	Debug bool
}

func Load() *Config {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}
	
	cfg := &Config{
		// Server
		ServerPort: getEnv("SERVER_PORT", "6003"),
		ServerHost: getEnv("SERVER_HOST", "0.0.0.0"),
		
		// OCR
		OCREngine:   getEnv("OCR_ENGINE", "surya"),
		OCRLanguage: getEnv("OCR_LANGUAGE", "kor+eng"),
		UseGPU:      getEnvBool("USE_GPU", false),
		
		// PDF
		PDFDpi: getEnvInt("PDF_DPI", 300),
		
		// LLM
		LLMBaseURL: getEnv("LLM_BASE_URL", "https://llm.gupsa.net/v1"),
		LLMAPIKey:  getEnv("LLM_API_KEY", ""),
		LLMModel:   getEnv("LLM_MODEL", "boto"),
		
		// Storage
		OutputDir:   getEnv("OUTPUT_DIR", "output"),
		CacheDir:    getEnv("CACHE_DIR", "cache"),
		TemplateDir: getEnv("TEMPLATE_DIR", "templates"),
		DemoDir:     getEnv("DEMO_DIR", "demo"),
		
		// Performance
		MaxWorkers:        getEnvInt("MAX_WORKERS", 4),
		EnableCompression: getEnvBool("ENABLE_COMPRESSION", true),
		
		// Debugging
		Debug: getEnvBool("DEBUG", false),
	}
	
	// Validate required fields (LLM API Key는 선택사항으로 변경)
	if cfg.LLMAPIKey == "" {
		log.Println("Warning: LLM_API_KEY not set, LLM features may not work")
	}
	
	return cfg
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}

func (c *Config) GetAddress() string {
	return fmt.Sprintf("%s:%s", c.ServerHost, c.ServerPort)
}
