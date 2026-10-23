from pydantic import BaseModel
from datetime import datetime


class ConnectionReadModel(BaseModel):
    """Acts as the data contract between the frontend and the backend.

    It defines the JSON structure used to exchange connection information,
    ensuring data consistency and validation during API requests and responses."""

    id_player: str | None = None
    id_user: str
    timestamp: datetime