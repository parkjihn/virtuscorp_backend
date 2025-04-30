from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from app.schemas.user import UserCreate, UserLogin
from app.crud.user import create_user, verify_user, get_user_by_email
from app.utils.helpers import create_access_token
from app.models.user import User
from datetime import datetime
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
        # Проверка пользователя из базы
        user_db = await verify_user(user.email, user.password)
        if not user_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Update last login time
        user_db.last_login = datetime.utcnow()
        await user_db.save()

        # Генерация токена
        token = create_access_token({"sub": user_db.email})
        
        # Создаем JSON-ответ
        content = {
            "message": "Login successful",
            "access_token": token
        }
        
        # Создаем response с правильными настройками CORS
        response = JSONResponse(content=content)
        
        # Устанавливаем cookie с правильными настройками
        response.set_cookie(
            key="auth-token",
            value=token,
            httponly=True,  # Для безопасности в продакшене
            secure=False,   # Установите True в продакшене с HTTPS
            samesite="lax", # Более безопасная настройка, работает в большинстве браузеров
            path="/",
            max_age=3600    # 1 час
        )
        
        return response
        
    except Exception as e:
        # Логирование ошибок
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
