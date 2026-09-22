from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=10, description="Google ID token from GIS")


class PasswordLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)



class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    google_id: str
    role: int
    picture_url: str | None = None

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str
    user: UserResponse
