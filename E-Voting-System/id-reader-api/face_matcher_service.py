"""
face_matcher_service.py
-----------------------
Face-matching pipeline extracted from ID_matcher.ipynb.

Uses RetinaFace for face detection/landmark extraction and DeepFace
(ArcFace model) for computing face embeddings.  Cosine similarity is
then used to decide whether two photos show the same person.

The DeepFace model weights are downloaded automatically on first use
(~50 MB for ArcFace).  Subsequent calls use the cached weights.
"""

import cv2
import numpy as np
import tempfile
import os

# Heavy imports — loaded once at module level so the server pays the
# startup cost only once, not on every request.
from retinaface import RetinaFace
from deepface import DeepFace


# ---------------------------------------------------------------------------
# Internal helpers (mirror the notebook cells)
# ---------------------------------------------------------------------------

def _face_detection(img_path: str) -> dict:
    """
    Detect exactly one face in the image at *img_path*.

    Raises
    ------
    ValueError
        If zero or more than one face is found.
    """
    faces = RetinaFace.detect_faces(img_path)
    if not faces:
        raise ValueError("No face detected in the image.")
    valid_faces = list(faces.values())
    if len(valid_faces) > 1:
        raise ValueError("More than one face detected in the image.")
    return valid_faces[0]


def _is_face_straight(face: dict, max_angle: float = 10.0) -> bool:
    """Return True if the face tilt angle is within *max_angle* degrees."""
    landmarks = face["landmarks"]
    left_eye, right_eye = landmarks["left_eye"], landmarks["right_eye"]
    dy = left_eye[1] - right_eye[1]
    dx = left_eye[0] - right_eye[0]
    angle = abs(np.degrees(np.arctan2(dy, dx)))
    return angle <= max_angle


def _crop_face_with_margin(img: np.ndarray, face: dict, margin: float = 0.5) -> np.ndarray:
    """Crop the detected face region with a proportional margin."""
    h, w = img.shape[:2]
    x1, y1, x2, y2 = face["facial_area"]

    bw, bh = x2 - x1, y2 - y1
    mx, my = int(bw * margin), int(bh * margin)

    x1 = max(0, x1 - mx)
    y1 = max(0, y1 - my)
    x2 = min(w, x2 + mx)
    y2 = min(h, y2 + my)

    return img[y1:y2, x1:x2]


def _face_alignment(img: np.ndarray, face: dict) -> np.ndarray:
    """Rotate *img* so that the eye-line is horizontal."""
    landmarks = face["landmarks"]
    left_eye = landmarks["left_eye"]
    right_eye = landmarks["right_eye"]

    dy = left_eye[1] - right_eye[1]
    dx = left_eye[0] - right_eye[0]
    angle = np.degrees(np.arctan2(dy, dx))

    h, w = img.shape[:2]
    eye_center = (
        int((left_eye[0] + right_eye[0]) / 2),
        int((left_eye[1] + right_eye[1]) / 2),
    )

    M = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h))


def _img_preprocessing(img_path: str) -> np.ndarray:
    """
    Full preprocessing pipeline (mirrors the notebook):
      1. Read image from disk.
      2. Detect face → align → re-detect → crop with margin.
      3. Convert to grayscale then back to 3-channel RGB
         (DeepFace expects 3-channel input).
    """
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError("Failed to read image from path.")

    face = _face_detection(img_path)
    aligned = _face_alignment(img, face)

    # Write aligned image to a temp file so RetinaFace can re-detect
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    cv2.imwrite(tmp_path, aligned)

    try:
        face2 = _face_detection(tmp_path)
    finally:
        os.unlink(tmp_path)

    crop = _crop_face_with_margin(aligned, face2, margin=0.5)
    if crop.size == 0:
        raise ValueError("Face crop failed — the cropped region is empty.")

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return rgb


def _extract_embedding(img_path: str) -> np.ndarray:
    """
    Preprocess *img_path* and return its L2-normalised ArcFace embedding.
    """
    preprocessed = _img_preprocessing(img_path)
    result = DeepFace.represent(
        img_path=preprocessed,
        model_name="ArcFace",
        detector_backend="retinaface",
        enforce_detection=True,
    )
    embedding = np.array(result[0]["embedding"])
    return embedding / np.linalg.norm(embedding)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return the cosine similarity between two 1-D vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def match_faces(img1_path: str, img2_path: str, threshold: float = 0.45) -> dict:
    """
    Compare two face images and decide whether they belong to the same person.

    Parameters
    ----------
    img1_path : str
        Absolute path to the first image (e.g. ID-card photo).
    img2_path : str
        Absolute path to the second image (e.g. live selfie).
    threshold : float
        Minimum cosine similarity to consider a match. Default: 0.45.

    Returns
    -------
    dict with keys:
        success         (bool)  — True if processing succeeded
        is_same_person  (bool)  — True if similarity >= threshold
        similarity      (float) — Raw cosine similarity score [−1, 1]
        threshold       (float) — Threshold used
        message         (str)   — Human-readable summary
    """
    emb1 = _extract_embedding(img1_path)
    emb2 = _extract_embedding(img2_path)
    sim = _cosine_similarity(emb1, emb2)
    same = sim >= threshold

    return {
        "success": True,
        "is_same_person": same,
        "similarity": round(sim, 6),
        "threshold": threshold,
        "message": (
            f"Faces match (similarity={sim:.4f} ≥ threshold={threshold})."
            if same
            else f"Faces do not match (similarity={sim:.4f} < threshold={threshold})."
        ),
    }
