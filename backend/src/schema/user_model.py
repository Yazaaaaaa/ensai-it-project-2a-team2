from datetime import datetime

from pydantic import BaseModel


class UserLoginModel(BaseModel):
    """Acts as the data contract between the frontend and the backend.

    It defines the JSON structure used to exchange connection information,
    ensuring data consistency and validation during API requests and responses.
    """

    id_player: str
    password: str


class ConnectionReadModel(BaseModel):
    """Acts as the data contract between the frontend and the backend.

    It defines the JSON structure used to exchange connection information,
    ensuring data consistency and validation during API requests and responses."""

    id_login: str | None = None
    id_user: str
    login_at: datetime | None = None

    class Config:
        from_attributes = True
