import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from app.i18n_keys import I18nKeys

load_dotenv()

# Config Cloudinary tu CLOUDINARY_URL trong .env
# Format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL")
)

class CloudinaryService:
    
    @staticmethod
    def upload_image(file: UploadFile, folder: str = "products") -> dict:
        """
        Upload image to Cloudinary
        Returns: dict with public_id, secure_url, etc.
        """
        try:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400, 
                    detail=I18nKeys.UPLOAD_INVALID_TYPE
                )
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file.file,
                folder=folder,
                resource_type="image",
                transformation=[
                    {"width": 800, "height": 800, "crop": "limit"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            
            return {
                "public_id": result.get("public_id"),
                "url": result.get("secure_url"),
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format")
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=I18nKeys.UPLOAD_FAILED)
    
    @staticmethod
    def delete_image(public_id: str) -> bool:
        """
        Delete image from Cloudinary by public_id
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as e:
            raise HTTPException(status_code=500, detail=I18nKeys.UPLOAD_FAILED)
