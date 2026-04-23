"""
main.py
-------
FastAPI server for the E-Voting-System ID-Number-Reader microservice.

Endpoints
---------
GET  /          → health check
POST /extract-id → accepts an image upload, returns the extracted ID number
"""

import io

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ocr_service import extract_id_number

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ID Number Reader API",
    description=(
        "Upload a photo of an Egyptian national ID card and receive the "
        "extracted 14-digit ID number in both Arabic-Indic and Western formats."
    ),
    version="1.0.0",
)

# Allow all origins during development so the .NET front-end can call freely.
# Restrict `allow_origins` to your actual domain(s) in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Accepted image MIME types
_ALLOWED_CONTENT_TYPES = {
    "image/png",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _bytes_to_cv2(data: bytes) -> np.ndarray:
    """Decode raw image bytes into a BGR OpenCV image."""
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """
    Simple health-check endpoint.

    Returns `{ "status": "ok" }` when the server is running.
    """
    return {"status": "ok", "message": "ID Number Reader API is running."}


@app.post("/extract-id", tags=["OCR"])
async def extract_id(image: UploadFile = File(..., description="Image of the national ID card")):
    """
    Extract the national ID number from an uploaded ID card image.

    **Accepts:** JPEG, PNG, WebP, BMP, TIFF (multipart/form-data)

    **Returns:**
    ```json
    {
        "success": true,
        "id_number_arabic":  "٣٠٥٠٤١١٠٢٠٣٧",
        "id_number_english": "30504110203 7",
        "raw_ocr_text": "...",
        "message": "ID number extracted successfully (14 digits)."
    }
    ```
    """
    # --- Validate content type -------------------------------------------
    content_type = image.content_type or ""
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{content_type}'. "
                f"Please upload one of: {', '.join(sorted(_ALLOWED_CONTENT_TYPES))}"
            ),
        )

    # --- Read & decode image ---------------------------------------------
    raw_bytes = await image.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    img = _bytes_to_cv2(raw_bytes)
    if img is None:
        raise HTTPException(
            status_code=400,
            detail="Could not decode the uploaded image. Make sure it is a valid image file.",
        )

    # --- Run OCR pipeline ------------------------------------------------
    result = extract_id_number(img)

    if not result["success"]:
        # We found the image but couldn't extract a number → 422
        raise HTTPException(
            status_code=422,
            detail=result["message"],
        )

    return JSONResponse(content=result)
