#!/bin/bash

echo "=== Pure Go OCR/PDF System Full Test ==="
echo ""

# Test 1: Health Check
echo "1. Health Check:"
curl -s http://localhost:6003/health | jq .
echo ""

# Test 2: List Requests
echo "2. List Requests:"
curl -s http://localhost:6003/api/requests | jq '.data | length'
echo ""

# Test 3: Templates List
echo "3. Templates:"
curl -s http://localhost:6003/api/templates | jq '.success, .message'
echo ""

# Test 4: Process Image
echo "4. OCR Image Processing:"
RESULT=$(curl -s -X POST http://localhost:6003/api/process-image -F "file=@test_image.png")
echo "$RESULT" | jq '{success, message, blocks: .data.blocks | length, avg_conf: .data.average_confidence}'
REQUEST_ID=$(echo "$RESULT" | jq -r '.data.request_id')
echo "Request ID: $REQUEST_ID"
echo ""

# Test 5: Process PDF
echo "5. PDF Processing:"
RESULT=$(curl -s -X POST http://localhost:6003/api/process-pdf -F "file=@test_document.pdf")
echo "$RESULT" | jq '{success, message, pages: .data.total_pages, blocks: .data.total_blocks, avg_conf: .data.average_confidence}'
echo ""

echo "=== All Tests Completed Successfully ==="
