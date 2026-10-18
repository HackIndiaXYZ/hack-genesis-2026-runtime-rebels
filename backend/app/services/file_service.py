import os
import io
import uuid
from pathlib import Path
from PIL import Image
from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".avi"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def save_upload_file(file: UploadFile) -> str:
    """
    Validates and saves an uploaded image/video.
    Returns relative URL path (e.g. '/uploads/<filename>').
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File exceeds maximum allowed size of 10 MB ({len(content) / (1024 * 1024):.1f} MB)."
        )

    # Validate image readability
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        try:
            with Image.open(io.BytesIO(content)) as img:
                img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file is corrupted or not a valid image: {e}"
            )

    # Reset position after reading
    await file.seek(0)

    # 1. Cloud Storage Policy: Enforce persistent storage in production
    is_production = os.getenv("ENVIRONMENT") == "production" or os.getenv("REQUIRE_CLOUD_STORAGE", "").lower() == "true"

    if is_production and not os.getenv("CLOUDINARY_URL"):
        raise HTTPException(
            status_code=500,
            detail="Persistent cloud storage is required in production, but CLOUDINARY_URL is not configured."
        )

    if os.getenv("CLOUDINARY_URL"):
        try:
            import cloudinary
            import cloudinary.uploader
            upload_res = cloudinary.uploader.upload(
                io.BytesIO(content),
                folder="civicfix_complaints",
                public_id=uuid.uuid4().hex,
                resource_type="auto"
            )
            secure_url = upload_res.get("secure_url")
            if secure_url:
                return secure_url
            raise RuntimeError("Cloudinary service did not return a secure_url.")
        except Exception as e:
            if is_production:
                raise HTTPException(
                    status_code=502,
                    detail=f"Cloud image storage failed: {e}. Ephemeral disk fallback is disabled in production to protect evidence."
                )
            print(f"[FileService] Cloudinary upload failed ({e}), falling back to local disk in dev mode.")

    # 2. Local Disk Storage (Default for local development only)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = UPLOAD_DIR / unique_filename

    with open(dest_path, "wb") as buffer:
        buffer.write(content)

    return f"/uploads/{unique_filename}"
