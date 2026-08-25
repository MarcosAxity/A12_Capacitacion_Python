from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["admin"])
    email: EmailStr
    full_name: str | None = None


class UserOut(UserBase):
    disabled: bool = False


class UserLogin(BaseModel):
    username: str
    password: str = Field(..., min_length=4)
