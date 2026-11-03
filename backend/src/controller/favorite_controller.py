from fastapi import APIRouter

from schema.favorite_schema import FavoriteIn, FavoriteOut, _favorite_to_out
from service.favorite_service import FavoriteService

router = APIRouter()


@router.post("", response_model=FavoriteOut, status_code=201)
def add_favorite(body: FavoriteIn):
    """Adds a NEO to the favorites of a user."""
    favorite, neo = FavoriteService().add(body.id_user, body.id_neo)
    return _favorite_to_out(favorite, neo)


@router.get("/{id_user}", response_model=list[FavoriteOut])
def list_favorites(id_user: int):
    """Lists the favorites of a user (most recent first), each with its NEO."""
    favorites = FavoriteService().list_favorites(id_user)
    return [_favorite_to_out(f, n) for f, n in favorites]


@router.delete("/{id_user}/{id_neo}", status_code=204)
def remove_favorite(id_user: int, id_neo: int):
    """Removes a NEO from the favorites of a user."""
    FavoriteService().remove(id_user, id_neo)