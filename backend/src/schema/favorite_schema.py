from datetime import datetime

from pydantic import BaseModel

from business_object.favorite import Favorite
from business_object.neo import Neo
from schema.neo_schema import NeoOut, _to_out


class FavoriteIn(BaseModel):
    """Body to add a NEO to the favorites of a user."""
    id_user: int
    id_neo: int


class FavoriteOut(BaseModel):
    """Favorite returned by the API, with the NEO it refers to."""
    id_favorite: int | None
    id_user: int
    id_neo: int
    added_at: datetime | None
    neo: NeoOut


def _favorite_to_out(favorite: Favorite, neo: Neo) -> FavoriteOut:
    """Converts a Favorite and its Neo into their API representation."""
    return FavoriteOut(
        id_favorite=favorite.id_favorite,
        id_user=favorite.id_user,
        id_neo=favorite.id_neo,
        added_at=favorite.added_at,
        neo=_to_out(neo),
    )