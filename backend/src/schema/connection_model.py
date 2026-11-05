from datetime import datetime

from pydantic import BaseModel


class ConnectionReadModel(BaseModel):
    """Acts as the data contract between the frontend and the backend.

    It defines the JSON structure used to exchange connection information,
    ensuring data consistency and validation during API requests and responses."""

    id_login: int | None = None
    id_user: int | None = None
    login_at: datetime | None = None

    class Config:
        from_attributes = True
