from fastapi import APIRouter, Depends, Response
from schema.favorite_schema import FavoriteIn, FavoriteOut, _favorite_to_out
from service.favorite_service import FavoriteService
from business_object.user import User
from controller.dependencies import get_current_user

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


@router.get("/{id_neo}/distances")
def get_distances(
    id_neo: int,
    orbiting_body: str | None = "Earth",
    current_user: User = Depends(get_current_user),
):
    """Returns the miss distances of a favorite NEO over time."""
    return FavoriteService().get_distance_history(current_user.id_user, id_neo, orbiting_body)


@router.get("/{id_neo}/distances/chart", response_class=Response)
def get_distances_chart(
    id_neo: int,
    orbiting_body: str | None = "Earth",
    current_user: User = Depends(get_current_user),
):
    """Returns a PNG chart of the miss distances of a favorite NEO."""
    png = FavoriteService().render_distance_chart(current_user.id_user, id_neo, orbiting_body)
    return Response(content=png, media_type="image/png")