# PageReader

A lightweight offline desktop app that reads structured form data from images using OCR and exports it directly to Excel. Built with Python — no internet connection required, all data stays on your machine.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Tesseract](https://img.shields.io/badge/OCR-Tesseract%205.x-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Features
- 📷 Load a photo of a form → fields auto-extracted via Tesseract OCR
- ✏️ Review and edit extracted fields before saving
- 📊 Appends records to a local Excel file (`output/data.xlsx`)
- 🔢 SR.NO auto-assigned — no manual numbering needed
- 🌐 Supports mixed English + Marathi text
- 📡 Webcam capture support (connect webcam and it works automatically)
- 🔒 100% offline — no data leaves your PC

## Fields Captured
`SR.NO` · `NAME` · `VILLAGE` · `MOBILE.NO` · `AADHAAR.NO` · `AP.DATE` · `CENTER`

## Requirements
- Python 3.10+
- Tesseract OCR 5.x

## Installation

### 1. Install Tesseract OCR
Download the Windows installer from:
👉 https://github.com/UB-Mannheim/tesseract/wiki

After installing, add Tesseract to your system PATH. If you skip this step, set the path manually in `src/ocr.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\<username>\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
```

### 2. Clone the repository
```bash
git clone https://github.com/VedantRSavdekar/PageReader.git
cd PageReader
```

### 3. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the app
```bash
python main.py
```

## Usage
1. Click **Load Image** → select a photo of your form
2. Wait for OCR to complete → fields auto-populate
3. Review and correct any fields if needed
4. Click **Save to Excel** → record is appended to `output/data.xlsx`
5. Click **Clear Fields** → ready for the next entry

## Privacy
- All OCR processing runs locally via Tesseract (no cloud API)
- The `output/` folder is listed in `.gitignore` — your Excel data is never pushed to GitHub

## Tech Stack
- [OpenCV](https://opencv.org/) — webcam capture
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — text recognition
- [pytesseract](https://github.com/madmaze/pytesseract) — Python wrapper for Tesseract
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel file handling
- [Pillow](https://pillow.readthedocs.io/) — image processing
- [Tkinter](https://docs.python.org/3/library/tkinter.html) — desktop UI

## Author
**Vedant Savdekar** — [GitHub](https://github.com/VedantRSavdekar)
