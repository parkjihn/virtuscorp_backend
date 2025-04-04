from datetime import datetime, timedelta
from jose import jwt
import os

# Get the secret key from environment variable or use a more secure default
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a_much_more_secure_secret_key_that_is_at_least_32_characters")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

