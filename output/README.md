# Output Directory

This directory contains the results of OCR processing.

## Hierarchical Structure

### New Format (Organized)
- `pdfs/YYYY-MM-DD/filename_HHMMSS/`
  - `page_N/` - Individual page results
    - `result.json` - OCR results with blocks
    - `visualization.png` - Annotated image
  - `summary.json` - PDF summary information

- `images/YYYY-MM-DD/filename_HHMMSS/`
  - `result.json` - OCR results with blocks
  - `visualization.png` - Annotated image

- `documents/YYYY-MM-DD/filename_HHMMSS/`
  - General document processing results

### Legacy Format (Flat)
- `filename_YYYYMMDD_HHMMSS_result.json` - OCR results
- `filename_YYYYMMDD_HHMMSS_visualization.png` - Annotated images

## API Access

All files can be accessed via the API:

```bash
# List all files
curl http://localhost:6003/output/list

# Get file statistics
curl http://localhost:6003/output/stats

# Download specific file
curl http://localhost:6003/output/download/filename.json
```

## Note

Actual output files are not tracked in git to keep the repository clean.
Only the directory structure and documentation are included.