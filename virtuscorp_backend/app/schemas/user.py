from pydantic import BaseModel, EmailStr, model_validator

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @model_validator(mode='after')
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
