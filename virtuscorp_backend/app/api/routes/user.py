from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserProfileResponse
from app.utils.helpers import get_current_user
import os
from datetime import datetime
import uuid
import shutil

router = APIRouter()

UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Maximum file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile"""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "position": current_user.position,
        "department": current_user.department,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "last_login": current_user.last_login
    }

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the current user's profile"""
    # Update only the fields that are provided
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.position is not None:
        current_user.position = profile_data.position
    if profile_data.department is not None:
        current_user.department = profile_data.department
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url
    
    await current_user.save()
    
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "position": current_user.position,
        "department": current_user.department,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "last_login": current_user.last_login
    }

@router.post("/avatar", response_model=dict)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a new avatar for the current user"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if avatar.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
        )
    
    # Check file size
    contents = await avatar.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)}MB."
        )
    
    # Reset file position to start
    await avatar.seek(0)
    
    # Generate a unique filename
    file_ext = os.path.splitext(avatar.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    
    # Update the user's avatar_url
    avatar_url = f"/uploads/avatars/{unique_filename}"
    current_user.avatar_url = avatar_url
    await current_user.save()
    
    return {"avatar_url": avatar_url}
