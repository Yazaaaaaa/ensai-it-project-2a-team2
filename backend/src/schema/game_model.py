from pydantic import BaseModel


class GamePlayModel(BaseModel):
    id_opponent: int
    game_mode: str
    params: dict = {}


class GameResponse(BaseModel):
    username1: str
    username2: str
    description: str
    winner: str | None
    new_elo1: int
    new_elo2: int