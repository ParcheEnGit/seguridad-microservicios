from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=10, description="Google ID token from GIS")


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    google_id: str

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str
    user: UserResponse
