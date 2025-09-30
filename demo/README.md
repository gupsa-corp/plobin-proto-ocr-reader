# Demo Files

This directory contains sample files for testing the OCR API.

## Structure

- `invoices/` - Sample invoice PDF files
- `receipts/` - Sample receipt images
- `business/` - Business document samples
- `processed/` - Pre-processed sample files for quick testing

## Usage

Upload any of these files to test the API endpoints:

```bash
# Test with invoice PDF
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/process-pdf

# Test with business report image
curl -X POST -F "file=@demo/processed/business/images/sample_business_report_page_001.png" http://localhost:6003/process-image
```

## Note

Large binary files (.pdf, .png, .jpg) are not included in the repository to keep it lightweight.
The folder structure is preserved for reference.