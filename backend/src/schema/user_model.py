from datetime import datetime
from pydantic import BaseModel, Field


class UserLoginModel(BaseModel):
    email: str
    password: str


class UserCreateModel(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role: str


class UserResponseModel(BaseModel):
    """Ne contient jamais password_hash ni token."""
    id_user: int
    email: str
    role_user: str
    created_at: datetime | None = None
