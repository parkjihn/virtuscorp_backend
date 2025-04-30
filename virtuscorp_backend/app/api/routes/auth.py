# app/api/routes/auth.py - Optimized version

from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from app.schemas.user import UserCreate, UserLogin
from app.crud.user import create_user, verify_user, get_user_by_email
from app.utils.helpers import create_access_token
from app.models.user import User
from datetime import datetime, timezone
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
async def register(user: UserCreate):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing = await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = await create_user(user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email,
        }
    }


@router.post("/login")
async def login(user: UserLogin, request: Request):
    try:
        # Verify the user against the database
        user_db = await verify_user(user.email, user.password)
        if not user_db:
            # Return 401 directly instead of raising an exception that gets caught later
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid credentials"}
            )

        # Update last login time - with error handling for missing column
        try:
            # Fix: Use timezone-aware datetime
            user_db.last_login = datetime.now(timezone.utc)
            await user_db.save()
        except Exception as e:
            # Log the error but don't fail the login process
            logger.warning(f"Could not update last_login: {str(e)}")

        # Generate token
        token = create_access_token({"sub": user_db.email})
        
        # Create response content
        content = {
            "message": "Login successful",
            "access_token": token
        }
        
        # Create response with proper cookie settings
        response = JSONResponse(content=content)
        
        # Set secure cookie - this is critical for authentication
        response.set_cookie(
            key="auth-token",
            value=token,
            httponly=True,  # Improves security
            secure=True,    # For HTTPS
            samesite="lax", # Safer setting that works in most browsers
            path="/",
            max_age=86400   # 24 hours - increased from 1 hour
        )
        
        return response
        
    except Exception as e:
        # Log errors
        logger.error(f"Login error: {str(e)}")
        # Return 500 error with details
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
