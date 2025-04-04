from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.schemas.user import UserCreate, UserLogin
from app.crud.user import create_user, verify_user, get_user_by_email
from app.utils.helpers import create_access_token
import os

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate):
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
async def login(user: UserLogin):
    # 🔐 Мастер-доступ
    if user.email == "admin@example.com" and user.password == "admin1234":
        token = create_access_token({"sub": user.email})
        response = JSONResponse(content={"message": "Login successful (admin)"})
        response.set_cookie(
            key="auth-token",
            value=token,
            httponly=True,
            # Set secure to False for local development
            secure=os.environ.get("VERCEL_ENV") == "production",
            samesite="lax",
            max_age=3600,
            httponly=True,
        )
        return response

    # Проверка пользователя из БД
    user_db = await verify_user(user.email, user.password)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user_db.email})
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="auth-token",
        value=token,
        # Set secure to False for local development
        secure=os.environ.get("VERCEL_ENV") == "production",
        samesite="lax",
        max_age=3600,
        httponly=True,
    )
    return response

