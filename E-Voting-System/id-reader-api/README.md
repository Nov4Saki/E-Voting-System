# ID Number Reader API

A lightweight **FastAPI** microservice that accepts a photo of an Egyptian national ID card and returns the extracted 14-digit national ID number in both Arabic-Indic and Western (0–9) formats.

This service is part of the **E-Voting-System** project and is designed to run alongside the ASP.NET Core application.

---

## Project Structure

```
id-reader-api/
├── main.py           # FastAPI application & route definitions
├── ocr_service.py    # OCR pipeline (EasyOCR + OpenCV preprocessing)
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.9+ |
| pip | 21+ |

> ℹ️ No virtual environment is required. All packages are installed globally.

---

## Installation

Open a terminal, navigate to this directory, and run:

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server to run FastAPI |
| `python-multipart` | Enables file upload parsing |
| `easyocr` | Arabic OCR engine |
| `opencv-python` | Image preprocessing |
| `numpy` | Array operations for image decoding |

> ⚠️ **First run note:** EasyOCR will automatically download its Arabic language model (~150 MB) the first time the server starts. This only happens once; the model is cached locally afterward.

---

## Running the Server

From inside the `id-reader-api/` directory:

```bash
uvicorn main:app --reload --port 8000
```

| Flag | Effect |
|---|---|
| `--reload` | Auto-restarts the server when you save a file (development mode) |
| `--port 8000` | Runs on port 8000 (change if needed) |

The server will be available at: **http://localhost:8000**

---

## API Reference

### `GET /`
Health check — confirms the server is running.

**Response:**
```json
{
  "status": "ok",
  "message": "ID Number Reader API is running."
}
```

---

### `POST /extract-id`
Upload an ID card image and receive the extracted ID number.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `image` | File | The ID card photo (JPEG, PNG, WebP, BMP, or TIFF) |

**Success Response (200):**
```json
{
  "success": true,
  "id_number_arabic":  "٣٠٥٠٤١١٠٢٠٣٧٦",
  "id_number_english": "30504110203776",
  "raw_ocr_text": "٣٠٥٠٤١١٠٢٠٣٧٦ ...",
  "message": "ID number extracted successfully (14 digits)."
}
```

**Error Responses:**

| Code | Cause |
|---|---|
| `400` | Invalid file type or unreadable/corrupt image |
| `422` | Image was valid but no ID number could be found |
| `500` | Unexpected server error |

---

## Testing

### Option 1 — Swagger UI (recommended)

1. Start the server.
2. Open **http://localhost:8000/docs** in your browser.
3. Click `POST /extract-id` → **Try it out**.
4. Upload your ID card image and click **Execute**.

### Option 2 — cURL

```bash
curl -X POST "http://localhost:8000/extract-id" \
     -H "accept: application/json" \
     -F "image=@path/to/your/id_card.jpg"
```

### Option 3 — PowerShell

```powershell
$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/extract-id" `
    -Method Post `
    -Form @{ image = Get-Item "path\to\your\id_card.jpg" }

$response | ConvertTo-Json
```

---

## Calling from the ASP.NET Front-End

Use `HttpClient` to POST the image as `multipart/form-data`:

```csharp
using var client = new HttpClient();
using var content = new MultipartFormDataContent();
content.Add(new StreamContent(imageStream), "image", "id_card.jpg");

var response = await client.PostAsync("http://localhost:8000/extract-id", content);
var json = await response.Content.ReadAsStringAsync();
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'easyocr'`
Run `pip install -r requirements.txt` again and make sure you're using the same Python installation where pip installed the packages.

### `Address already in use` on port 8000
Either change the port:
```bash
uvicorn main:app --reload --port 8080
```
Or find and stop the process using port 8000:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### EasyOCR model download fails
Make sure you have an internet connection on first startup. The model is saved to `~/.EasyOCR/model/`.

### Low OCR accuracy
- Use a well-lit, high-resolution photo of the ID card.
- Avoid motion blur or heavy glare.
- Ensure the ID number is not obscured.

---

## Production Notes

- Remove the `--reload` flag when deploying.
- Restrict CORS origins in `main.py` (`allow_origins=["https://your-domain.com"]`).
- Consider running behind a reverse proxy (e.g., nginx) with HTTPS.
