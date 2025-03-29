from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserLogin
from app.crud.user import create_user, verify_user, get_user_by_email
from app.utils.helpers import create_access_token

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
            "language": new_user.language,
            "timezone": new_user.timezone,
            "theme": new_user.theme,
            "profile_picture": new_user.profile_picture,
            "is_active": new_user.is_active,
        }
    }


@router.post("/login")
async def login(user: UserLogin):
    # 🔐 Мастер-доступ
    if user.email == "admin@example.com" and user.password == "admin1234":
        token = create_access_token({"sub": user.email})
        return {"access_token": token, "token_type": "bearer"}

    # Обычная проверка из базы
    user_db = await verify_user(user.email, user.password)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user_db.email})
    return {"access_token": token, "token_type": "bearer"}
