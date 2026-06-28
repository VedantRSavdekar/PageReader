# OCR to Excel

A local desktop app that reads structured form data from images (or webcam) using OCR and saves it to Excel — all offline, no data leaves your PC.

## Features
- Load a photo of a form → auto-extract fields via Tesseract OCR
- Review and edit extracted fields before saving
- Saves to a local Excel file (`output/data.xlsx`)
- SR.NO auto-assigned (no need to read it from the page)
- Webcam capture support (plug in and it works automatically)

## Fields Captured
`SR.NO` · `NAME` · `VILLAGE` · `MOBILE.NO` · `AADHAAR.NO` · `AP.DATE` · `CENTER`

## Setup

### 1. Install Tesseract OCR
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract to your system PATH, or set the path in `src/ocr.py`

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python main.py
```

## Usage
1. Click **Load Image** → select a photo of the form
2. Wait for OCR to finish → fields auto-populate
3. Review and correct any fields if needed
4. Click **Save to Excel** → record is appended to `output/data.xlsx`
5. Click **Clear Fields** → ready for next page

## Privacy
- All processing is 100% local (Tesseract runs offline)
- `output/` folder is in `.gitignore` — Excel data is never pushed to GitHub
