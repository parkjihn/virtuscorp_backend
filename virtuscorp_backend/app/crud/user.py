from passlib.context import CryptContext
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user_by_email(email: str):
    return await User.get_or_none(email=email)

async def create_user(user_data):
    hashed_password = pwd_context.hash(user_data.password)
    return await User.create(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password,  # Changed from hashed_password to password_hash
    )


async def verify_user(email: str, password: str):
    user = await get_user_by_email(email)
    if user and pwd_context.verify(password, user.password_hash):  # Changed from hashed_password to password_hash
        return user
    return None
