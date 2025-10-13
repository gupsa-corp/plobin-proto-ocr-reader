#!/bin/bash
curl -s -X POST http://localhost:6003/api/process-pdf \
  -F "file=@test_document.pdf" | jq . | head -80
