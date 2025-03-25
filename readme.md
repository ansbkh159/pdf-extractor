# PDF to Markdown Converter

A robust tool that extracts text, tables, and images from PDFs and converts them into structured Markdown files. Uses PyMuPDF for primary extraction and Tesseract OCR as a fallback for problematic content.

## 🛠 Installation

### Python Dependencies

pip install -r requirements.txt
pip install -e .

### System dependencies Dependencies

Tesseract OCR: Required for handling scanned/OCR content

Windows: https://github.com/UB-Mannheim/tesseract/wiki

MacOS: brew install tesseract

Linux: sudo apt install tesseract-ocr


### 🚀 Usage


python main.py <path_to_input.pdf> <output>

Example:
python main.py document.pdf result

### How this works

The pipeline first extracts raw content using PyMuPDF, retrieving text blocks, tables, and images with their precise page coordinates. After initial processing, the system performs a full document re-scan to validate consistency. When mismatches are detected, it logs the problematic page numbers and triggers targeted Tesseract OCR reprocessing only for those pages. The OCR results undergo coordinate alignment to match the original document structure before being merged with the initial extraction data. This hybrid output then feeds into a Markdown generator that applies layout-aware formatting. The entire process runs via python main.py input.pdf output.md, automatically handling the OCR fallback without user intervention.