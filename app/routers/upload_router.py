from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.cloudinary_service import CloudinaryService
from app.services.user_service import require_user
from app.models.sqlalchemy.user import User

upload_router = APIRouter()


@upload_router.post("/upload/return-evidence")
async def upload_return_evidence(
    file: UploadFile = File(...),
    current_user: User = Depends(require_user)
):
    """
    Upload return evidence image/video to Cloudinary
    Returns: { url, public_id, width, height, format }
    """
    # Validate file type - allow images and videos
    allowed_types = [
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "video/mp4", "video/webm", "video/quicktime"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: images (jpeg, png, webp, gif) and videos (mp4, webm, mov)"
        )
    
    # Upload to Cloudinary
    is_video = file.content_type.startswith("video/")
    folder = "return_evidence"
    
    if is_video:
        # Upload video without transformation
        import cloudinary.uploader
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="video"
        )
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "resource_type": "video"
        }
    else:
        # Upload image with optimization
        result = CloudinaryService.upload_image(file, folder=folder)
        return result
