.PHONY: help build run clean test lint deps dev

# Default target
help:
	@echo "Available targets:"
	@echo "  make build    - Build the application"
	@echo "  make run      - Run the application"
	@echo "  make dev      - Run in development mode"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make deps     - Download dependencies"
	@echo "  make lint     - Run linters"

# Build the application
build:
	@echo "Building application..."
	@mkdir -p bin
	@go build -o bin/server cmd/server/main.go
	@echo "Build complete: bin/server"

# Run the application
run: build
	@echo "Starting server..."
	@./bin/server

# Run in development mode
dev:
	@echo "Starting development server..."
	@go run cmd/server/main.go

# Run tests
test:
	@echo "Running tests..."
	@go test -v ./...

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	@go test -v -cover -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Clean build artifacts
clean:
	@echo "Cleaning..."
	@rm -rf bin
	@rm -f coverage.out coverage.html
	@echo "Clean complete"

# Download dependencies
deps:
	@echo "Downloading dependencies..."
	@go mod download
	@go mod tidy
	@echo "Dependencies updated"

# Run linters
lint:
	@echo "Running linters..."
	@if command -v golangci-lint > /dev/null; then \
		golangci-lint run; \
	else \
		echo "golangci-lint not found, skipping..."; \
		go fmt ./...; \
		go vet ./...; \
	fi

# Format code
fmt:
	@echo "Formatting code..."
	@go fmt ./...
	@echo "Format complete"

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	@go get -u ./...
	@go mod tidy
	@echo "Dependencies updated"
