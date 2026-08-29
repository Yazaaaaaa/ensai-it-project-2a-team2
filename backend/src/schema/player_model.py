from pydantic import BaseModel, EmailStr, field_validator


class PlayerModel(BaseModel):
    """Acts as the data contract between the frontend and the backend.

    It defines the JSON structure used to exchange player information,
    ensuring data consistency and validation during API requests and responses."""

    id_player: int | None = None
    username: str
    password: str
    elo: int
    email: EmailStr
    pokemon_fan: bool

    @field_validator("password")
    @classmethod
    def check_password_length(cls, v: str) -> str:
        min_len = 35
        if len(v) < min_len:
            raise ValueError(f"Password must be at least {min_len} characters long")
        return v


class PlayerReadModel(BaseModel):
    id_player: int
    username: str
    elo: int | None
    email: EmailStr
    pokemon_fan: bool | None


class PlayerLoginModel(BaseModel):
    username: str
    password: str