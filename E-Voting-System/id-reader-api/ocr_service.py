"""
ocr_service.py
--------------
Encapsulates the OCR pipeline from ID-Number-Reader.py as a reusable module.

The EasyOCR reader is initialised once as a module-level singleton so that
the expensive model-load (~3-5 s) only happens when the server starts, not
on every request.
"""

import re
import warnings

import cv2
import easyocr
import numpy as np

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Singleton OCR reader — loaded once at import time
# ---------------------------------------------------------------------------
print("[ocr_service] Loading EasyOCR Arabic model... (first run downloads ~150 MB)")
_reader = easyocr.Reader(["ar"], gpu=False)
print("[ocr_service] EasyOCR model ready.")

# Arabic-digit → ASCII-digit translation table
_ARABIC_TO_ENG = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# EasyOCR character allowlist — same as the original script
_ALLOWLIST = (
    "٠١٢٣٤٥٦٧٨٩"
    "ضصثقفغعهخحجدشسيبلاتنمكطئءؤرلاىةوزظآلآألألإإْذ~"
)


def preprocess(img: np.ndarray) -> np.ndarray:
    """
    Apply the same preprocessing pipeline as ID-Number-Reader.py:
      1. Resize 2× (INTER_CUBIC) for better OCR resolution.
      2. Convert to grayscale.
      3. Adaptive Gaussian thresholding (inverted: text = white).
      4. Dilation with a 3×3 rect kernel to thicken character strokes.
      5. Invert back → black text on white background.

    Parameters
    ----------
    img : np.ndarray
        BGR image as read by OpenCV.

    Returns
    -------
    np.ndarray
        Preprocessed single-channel image ready for EasyOCR.
    """
    # 1. Resize
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Adaptive threshold (inverted: text = white, background = black)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15, 6,
    )

    # 4. Dilate (thicken strokes so dots in Arabic digits connect)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thick_text = cv2.dilate(thresh, kernel, iterations=1)

    # 5. Invert → black text on white
    final_img = cv2.bitwise_not(thick_text)

    return final_img


def extract_id_number(img: np.ndarray) -> dict:
    """
    Run the full OCR pipeline on a BGR image and attempt to extract a
    national ID number (up to 14 Arabic/Eastern-Arabic digits).

    Parameters
    ----------
    img : np.ndarray
        BGR image as read by OpenCV.

    Returns
    -------
    dict with keys:
        success          (bool)   — True if a number was found
        id_number_arabic (str)    — Extracted number in Arabic-Indic digits
        id_number_english(str)    — Same number transliterated to 0-9
        raw_ocr_text     (str)    — Full concatenated OCR output (debug)
        message          (str)    — Human-readable status message
    """
    processed = preprocess(img)

    results = _reader.readtext(
        processed,
        detail=0,
        allowlist=_ALLOWLIST,
        width_ths=5.0,
    )

    full_text = "".join(results)

    # Extract sequences of Arabic-Indic digits (U+0660–U+0669)
    arabic_numbers = re.findall(r"[\u0660-\u0669]+", full_text)

    if not arabic_numbers:
        return {
            "success": False,
            "id_number_arabic": "",
            "id_number_english": "",
            "raw_ocr_text": full_text,
            "message": "No numeric sequence found in the image.",
        }

    # Take the longest sequence, capped at 14 digits
    id_arabic = max(arabic_numbers, key=len)[:14]
    id_english = id_arabic.translate(_ARABIC_TO_ENG)

    return {
        "success": True,
        "id_number_arabic": id_arabic,
        "id_number_english": id_english,
        "raw_ocr_text": full_text,
        "message": f"ID number extracted successfully ({len(id_arabic)} digits).",
    }
