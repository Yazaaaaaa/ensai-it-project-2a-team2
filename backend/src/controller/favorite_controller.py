from fastapi import APIRouter, Depends, Response

from business_object.user import User
from controller.dependencies import get_current_user
from schema.favorite_schema import FavoriteIn, FavoriteOut, _favorite_to_out
from service.favorite_service import FavoriteService

router = APIRouter()


@router.post("", response_model=FavoriteOut, status_code=201)
def add_favorite(body: FavoriteIn):
    """Adds a NEO to the favorites of a user.

    Args:
        body (FavoriteIn): Payload containing the user ID and NEO ID to bookmark.

    Returns:
        FavoriteOut: Serialized representation of the newly added favorite.

    Raises:
        HTTPException: 404 if the user or NEO does not exist, 409 if already in
            favorites, or 500 on persistence failure.
    """
    favorite, neo = FavoriteService().add(body.id_user, body.id_neo)
    return _favorite_to_out(favorite, neo)


@router.get("/{id_user}", response_model=list[FavoriteOut])
def list_favorites(id_user: int):
    """Lists the favorites of a user (most recent first), each with its NEO.

    Args:
        id_user (int): ID of the user whose favorites are retrieved.

    Returns:
        list[FavoriteOut]: Serialized list of the user's favorite NEOs.
    """
    favorites = FavoriteService().list_favorites(id_user)
    return [_favorite_to_out(f, n) for f, n in favorites]


@router.delete("/{id_user}/{id_neo}", status_code=204)
def remove_favorite(id_user: int, id_neo: int):
    """Removes a NEO from the favorites of a user.

    Args:
        id_user (int): ID of the user who owns the favorite.
        id_neo (int): ID of the NEO to remove from favorites.

    Raises:
        HTTPException: 404 if the NEO is not in the user's favorites.
    """
    FavoriteService().remove(id_user, id_neo)


@router.get("/{id_neo}/distances")
def get_distances(
    id_neo: int,
    orbiting_body: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Returns the miss distances of a favorite NEO over time.

    Args:
        id_neo (int): ID of the favorite NEO.
        orbiting_body (str | None): Optional celestial body filter (e.g., 'Earth').
        current_user (User): Authenticated user requesting the distance history.

    Returns:
        list: Chronological miss distance records for the favorite NEO.

    Raises:
        HTTPException: 404 if the NEO is not in the current user's favorites.
    """
    return FavoriteService().get_distance_history(current_user.id_user, id_neo, orbiting_body)


@router.get("/{id_neo}/distances/chart", response_class=Response)
def get_distances_chart(
    id_neo: int,
    orbiting_body: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Returns a PNG chart of the miss distances of a favorite NEO.

    Args:
        id_neo (int): ID of the favorite NEO to plot.
        orbiting_body (str | None): Optional celestial body filter (e.g., 'Earth').
        current_user (User): Authenticated user requesting the chart.

    Returns:
        Response: Raw PNG binary response with 'image/png' media type.

    Raises:
        HTTPException: 404 if the NEO is not in the current user's favorites or has no data.
    """
    # Return raw PNG bytes directly via FastAPI Response instead of JSON serialization
    png = FavoriteService().render_distance_chart(current_user.id_user, id_neo, orbiting_body)
    return Response(content=png, media_type="image/png")
