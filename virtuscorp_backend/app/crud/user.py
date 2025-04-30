from app.models.user import User
from app.schemas.user import UserCreate
import bcrypt
from datetime import datetime, timezone

async def get_user_by_email(email: str) -> User:
    """Get a user by email"""
    return await User.get_or_none(email=email)

async def create_user(user_data: UserCreate) -> User:
    """Create a new user"""
    # Hash the password
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Create the user
    user = await User.create(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        last_login=datetime.now(timezone.utc)
    )
    
    return user

async def verify_user(email: str, password: str) -> User:
    """Verify a user's credentials"""
    user = await get_user_by_email(email)
    if not user:
        return None
    
    # Check the password
    password_bytes = password.encode('utf-8')
    hashed_bytes = user.password_hash.encode('utf-8')
    
    if bcrypt.checkpw(password_bytes, hashed_bytes):
        return user
    
    return None
