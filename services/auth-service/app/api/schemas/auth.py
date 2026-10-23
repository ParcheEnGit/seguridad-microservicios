from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=10, description="Google ID token from GIS")


class PasswordLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)



class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    google_id: str | None
    role: int
    picture_url: str | None = None

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str
    user: UserResponse


class UserInviteCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    role: Literal[0, 1]


class UserRoleUpdate(BaseModel):
    role: Literal[0, 1]
