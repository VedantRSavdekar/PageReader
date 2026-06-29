import re
import pytesseract
from PIL import Image

# If Tesseract is not in PATH on Windows, uncomment and set your path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Users\admin\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

FIELD_KEYS = ["NAME", "VILLAGE", "MOBILE.NO", "AADHAAR.NO", "AP.DATE", "CENTER"]


def extract_text(image_path: str, lang: str = "eng+mar") -> str:
    """Run Tesseract OCR on image. Uses English + Marathi by default."""
    img = Image.open(image_path)
    # Resize for better OCR accuracy
    w, h = img.size
    if w < 1000:
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    config = r"--oem 3 --psm 6"
    return pytesseract.image_to_string(img, lang=lang, config=config)


def parse_letter(raw_text: str) -> dict:
    """
    Parse the printed Marathi letter.
    Extracts:
      - NAME: from line containing 'कामगाराचे नाव'
      - AP.DATE: first date pattern found (DD-MM-YYYY or DD/MM/YYYY)
      - CENTER: city name after 'केंद्र' or 'Kendra' or at end of address line
    """
    fields = {"NAME": "", "AP.DATE": "", "CENTER": ""}

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # NAME: look for 'नाव :' or 'nav :' followed by the name
        if ("नाव" in line or "naav" in line.lower() or "nav" in line.lower()) and ":" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                name = parts[-1].strip()
                # Strip leading punctuation OCR sometimes adds (', ", `, ')
                name = re.sub(r"^['\"`'']+", "", name).strip()
                if name:
                    fields["NAME"] = name

        # AP.DATE: find date pattern DD-MM-YYYY or DD/MM/YYYY
        if not fields["AP.DATE"]:
            date_match = re.search(r"\b(\d{2}[-/]\d{2}[-/]\d{4})\b", line)
            if date_match:
                fields["AP.DATE"] = date_match.group(1)

        # CENTER: city name appears after 'केंद्र ,' on the same line
        # e.g. "...जिल्हा कामगार सुविधा केंद्र , Dharangaon येथे..."
        # or on its own line as ",Dharangaon"
        if not fields["CENTER"]:
            center_match = re.search(r"केंद्र\s*[,،]?\s*([A-Z][a-zA-Z]+)", line)
            if center_match:
                fields["CENTER"] = center_match.group(1).strip()
            elif re.match(r"^[,،]?\s*([A-Z][a-zA-Z]{3,})$", line.strip()):
                solo = re.match(r"^[,،]?\s*([A-Z][a-zA-Z]{3,})$", line.strip())
                skip = {"Yours", "Dear", "Dated", "Subject", "Office", "India"}
                if solo and solo.group(1) not in skip:
                    fields["CENTER"] = solo.group(1)

    return fields


def parse_aadhaar(raw_text: str) -> dict:
    """
    Parse Aadhaar card image.
    Extracts:
      - AADHAAR.NO: 12-digit number (may be spaced as XXXX XXXX XXXX)
      - VILLAGE: from 'VTC: <village>' or best-guess from address lines
    """
    fields = {"AADHAAR.NO": "", "VILLAGE": ""}

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        # AADHAAR.NO: 12 digits possibly separated by spaces
        if not fields["AADHAAR.NO"]:
            aadhaar_match = re.search(r"\b(\d{4}\s?\d{4}\s?\d{4})\b", line)
            if aadhaar_match:
                # Normalize: remove spaces
                fields["AADHAAR.NO"] = aadhaar_match.group(1).replace(" ", "")

        # VILLAGE: explicit VTC label
        if not fields["VILLAGE"]:
            vtc_match = re.search(r"VTC\s*[:\-]\s*(.+)", line, re.IGNORECASE)
            if vtc_match:
                fields["VILLAGE"] = vtc_match.group(1).strip().rstrip(",")

    # If no VTC found, try to find village from address area
    # Aadhaar address is usually in the middle of the card
    # Look for a line that looks like a place name (not a number, not too long)
    if not fields["VILLAGE"]:
        for line in lines:
            # Skip lines with digits (pincode, aadhaar no), skip very long lines
            if re.search(r"\d", line):
                continue
            if len(line) > 40 or len(line) < 3:
                continue
            # Skip common non-village words
            skip = ["india", "government", "aadhaar", "आधार", "male", "female",
                    "dob", "जन्म", "year", "uid", "भारत"]
            if any(s in line.lower() for s in skip):
                continue
            fields["VILLAGE"] = line.strip().rstrip(",")
            break

    return fields


def process_letter(image_path: str) -> dict:
    """OCR pipeline for printed letter → NAME, AP.DATE, CENTER."""
    raw = extract_text(image_path, lang="eng+mar")
    return parse_letter(raw), raw


def process_aadhaar(image_path: str) -> dict:
    """OCR pipeline for Aadhaar card → AADHAAR.NO, VILLAGE."""
    raw = extract_text(image_path, lang="eng")
    return parse_aadhaar(raw), raw
