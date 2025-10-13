#!/bin/bash
curl -s -X POST http://localhost:6003/api/process-image \
  -F "file=@test_image.png" | jq .
