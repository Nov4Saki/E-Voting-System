"""
main.py
-------
FastAPI server for the E-Voting-System ID-Number-Reader microservice.

Endpoints
---------
GET  /             → health check
POST /extract-id   → accepts an image upload, returns the extracted ID number
POST /match-faces  → accepts two image uploads, returns whether they show the same person
"""

import io
import os
import tempfile

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ocr_service import extract_id_number
from face_matcher_service import match_faces

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
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/bmp",
    "image/tiff",
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


@app.post("/match-faces", tags=["Face Matching"])
async def match_face_images(
    id_photo: UploadFile = File(..., description="Photo from the ID card"),
    live_photo: UploadFile = File(..., description="Live selfie or capture to verify against the ID"),
    threshold: float = Query(default=0.45, ge=0.0, le=1.0, description="Cosine-similarity threshold (0–1). Higher → stricter match."),
):
    """
    Determine whether two face photos belong to the same person.

    The pipeline:
    1. Detect and align the face in each uploaded image using **RetinaFace**.
    2. Compute a normalised **ArcFace** embedding for each face.
    3. Compare embeddings via **cosine similarity**.
    4. Return a match decision based on the supplied `threshold`.

    **Accepts:** Two image files (JPEG, PNG, WebP, BMP, TIFF) via multipart/form-data.

    **Returns:**
    ```json
    {
        "success": true,
        "is_same_person": true,
        "similarity": 0.823456,
        "threshold": 0.45,
        "message": "Faces match (similarity=0.8235 ≥ threshold=0.45)."
    }
    ```
    """
    tmp_paths: list[str] = []
    try:
        for upload in (id_photo, live_photo):
            content_type = upload.content_type or ""
            if content_type not in _ALLOWED_CONTENT_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type '{content_type}' for '{upload.filename}'. "
                        f"Please upload one of: {', '.join(sorted(_ALLOWED_CONTENT_TYPES))}"
                    ),
                )

        for upload in (id_photo, live_photo):
            raw = await upload.read()
            if not raw:
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded file '{upload.filename}' is empty.",
                )
            # Write to a named temp file so RetinaFace (which needs a path) can read it
            suffix = os.path.splitext(upload.filename or ".jpg")[1] or ".jpg"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(raw)
                tmp_paths.append(tmp.name)

        result = match_faces(tmp_paths[0], tmp_paths[1], threshold=threshold)

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Face matching failed: {exc}")
    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    return JSONResponse(content=result)
