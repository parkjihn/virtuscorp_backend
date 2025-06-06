from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Request, HTTPException
from app.models.user import User

SECRET_KEY = "12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta=None):
    """
    Create a JWT access token with timezone-aware expiration.
    """
    to_encode = data.copy()
    # Use timezone-aware datetime objects
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request) -> User:
    """
    Get the current user from the request token.
    """
    token = request.cookies.get("auth-token") or request.headers.get("x-auth-token")
    if not token:
        print("Authentication error: No token provided")
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            print("Authentication error: Invalid token (no email in payload)")
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await User.get_or_none(email=email)
        if not user:
            print(f"Authentication error: User not found for email: {email}")
            raise HTTPException(status_code=401, detail="User not found")
        
        print(f"Successfully authenticated user: {user.id} ({user.email})")
        return user
    except JWTError as e:
        print(f"JWT decode error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
