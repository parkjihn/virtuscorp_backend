from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from app.schemas.user import UserCreate, UserLogin
from app.crud.user import create_user, verify_user, get_user_by_email
from app.utils.helpers import create_access_token
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

        # Генерация токена
        token = create_access_token({"sub": user_db.email})
        
        # Логирование для отладки
        logger.info(f"Login successful for user: {user.email}")
        logger.info(f"Generated token: {token[:10]}...")

        # Создаем обычный Response вместо JSONResponse
        response = Response(
            content=f'{{"message": "Login successful", "access_token": "{token}"}}',
            media_type="application/json"
        )
        
        # Устанавливаем cookie с минимальными ограничениями для отладки
        response.set_cookie(
            key="auth-token",
            value=token,
            httponly=False,  # Позволяем JavaScript читать куки для отладки
            secure=False,    # Работает без HTTPS
            samesite="none", # Наименее строгая настройка
            path="/"
        )
        
        # Логирование для отладки
        logger.info("Cookie set in response")
        
        return response
        
    except Exception as e:
        # Логирование ошибок
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
