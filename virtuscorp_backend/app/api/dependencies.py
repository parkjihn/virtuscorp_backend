from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError
from app.models.user import User
from app.utils.helpers import SECRET_KEY, ALGORITHM

async def get_current_user(request: Request) -> User:
    token = request.cookies.get("auth-token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await User.get_or_none(email=email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user
