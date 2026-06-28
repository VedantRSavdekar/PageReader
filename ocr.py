import re
import pytesseract
from PIL import Image

# If Tesseract is not in PATH on Windows, set the path here:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Fields we want to extract (in order)
FIELD_KEYS = ["NAME", "VILLAGE", "MOBILE.NO", "AADHAAR.NO", "AP.DATE", "CENTER"]


def extract_text_from_image(image_path: str) -> str:
    """Run Tesseract OCR on a given image file and return raw text."""
    img = Image.open(image_path)
    # Use LSTM engine + treat as a single block of text
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(img, config=custom_config)
    return text


def parse_fields(raw_text: str) -> dict:
    """
    Parse OCR text into structured fields.
    Expects lines like:
        NAME: John Doe
        VILLAGE: Wardha
        MOBILE.NO: 9876543210
        AADHAAR.NO: 1234 5678 9012
        AP.DATE: 01/06/2026
        CENTER: Nagpur
    Returns a dict with those keys.
    """
    fields = {key: "" for key in FIELD_KEYS}

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try to match "KEY: VALUE" or "KEY - VALUE" patterns
        match = re.match(
            r"(NAME|VILLAGE|MOBILE\.?NO|AADHAAR\.?NO|AP\.?DATE|CENT[ER]{2}R?)"
            r"\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE,
        )
        if match:
            raw_key = match.group(1).upper().replace(" ", "")
            value = match.group(2).strip()

            # Normalize key variants
            if "MOBILE" in raw_key:
                fields["MOBILE.NO"] = value
            elif "AADHAAR" in raw_key:
                fields["AADHAAR.NO"] = value
            elif "AP" in raw_key:
                fields["AP.DATE"] = value
            elif "CENT" in raw_key:
                fields["CENTER"] = value
            elif "VILLAGE" in raw_key:
                fields["VILLAGE"] = value
            elif "NAME" in raw_key:
                fields["NAME"] = value

    return fields


def process_image(image_path: str) -> dict:
    """Full pipeline: image → OCR → parsed fields."""
    raw_text = extract_text_from_image(image_path)
    fields = parse_fields(raw_text)
    return fields, raw_text
