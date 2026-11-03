from fastapi import HTTPException

from business_object.favorite import Favorite
from business_object.neo import Neo
from dao.favorite_dao import FavoriteDao
from dao.neo_dao import NeoDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class FavoriteService:
    """Service that manages the favorite NEOs of the users."""

    @log
    def add(self, id_user: int, id_neo: int) -> tuple[Favorite, Neo]:
        """Adds a NEO to the favorites of a user.
        Args:
            id_user (int): The id of the user.
            id_neo (int): The id of the NEO to add.
        Returns:
            tuple[Favorite, Neo]: The created favorite and the corresponding NEO.
        Raises:
            HTTPException: 404 if the NEO does not exist, 409 if it is already a favorite.
        """
        neo = NeoDao().find_by_id_neo(id_neo)
        if neo is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        dao = FavoriteDao()
        if dao.exists(id_user, id_neo):
            raise HTTPException(status_code=409, detail="NEO already in favorites")

        favorite = Favorite(id_user=id_user, id_neo=id_neo)
        if not dao.create(favorite):
            raise HTTPException(status_code=500, detail="The favorite could not be created")

        return favorite, neo

    @log
    def list_favorites(self, id_user: int) -> list[tuple[Favorite, Neo]]:
        """Lists the favorites of a user with their NEO, the most recent first.
        Args:
            id_user (int): The id of the user.
        Returns:
            list[tuple[Favorite, Neo]]: The favorites with their NEO (empty list if none).
        """
        neo_dao = NeoDao()
        result = []
        for favorite in FavoriteDao().find_all_by_user(id_user):
            neo = neo_dao.find_by_id_neo(favorite.id_neo)
            if neo is not None:
                result.append((favorite, neo))
        return result

    @log
    def remove(self, id_user: int, id_neo: int) -> bool:
        """Removes a NEO from the favorites of a user.
        Args:
            id_user (int): The id of the user.
            id_neo (int): The id of the NEO to remove.
        Returns:
            bool: True if the favorite was deleted.
        Raises:
            HTTPException: 404 if the NEO is not in the favorites of the user.
        """
        dao = FavoriteDao()
        favorite = next((f for f in dao.find_all_by_user(id_user) if f.id_neo == id_neo), None)
        if favorite is None:
            raise HTTPException(status_code=404, detail="Favorite not found")

        return dao.delete(favorite)