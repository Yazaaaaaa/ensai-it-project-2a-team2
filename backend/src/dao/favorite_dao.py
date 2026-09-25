from business_object.favorite import Favorite
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class FavoriteDao(metaclass=Singleton):
    """Class containing methods to access favorites in the database."""

    @log
    def create(self, favorite: Favorite) -> bool:
        """
        Adds a NEO to a user's favorites.

        Args:
            favorite (Favorite): The favorite to persist (user_id and neo_id).

        Returns:
            bool: True if the insertion is successful, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO NEOW.favorite (id_user, id_neo)
                        VALUES (%(id_user)s, %(id_neo)s)
                        RETURNING id_favorite, added_at;
                        """,
                        {"id_user": favorite.user_id, "id_neo": favorite.neo_id},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating favorite {favorite}: {e}")
            raise

        created = False
        if res:
            favorite.id = res["id_favorite"]
            favorite.added_at = res["added_at"]
            created = True

        return created

    @log
    def find_by_id(self, id_favorite: int) -> Favorite | None:
        """
        Retrieves a favorite from its id.

        Args:
            id_favorite (int): The id of the favorite.

        Returns:
            Favorite: The favorite if found, otherwise None.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM NEOW.favorite
                         WHERE id_favorite = %(id_favorite)s;
                        """,
                        {"id_favorite": id_favorite},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error finding favorite {id_favorite}: {e}")
            raise

        if not res:
            return None

        return Favorite(
            id=res["id_favorite"],
            user_id=res["id_user"],
            neo_id=res["id_neo"],
            added_at=res["added_at"],
        )

    @log
    def find_all_by_user(self, id_user: int) -> list[Favorite]:
        """
        Returns all the favorites of a user, the most recent first.

        Args:
            id_user (int): The id of the user.

        Returns:
            list[Favorite]: The user's favorites (empty list if none).
        """
        rows = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM NEOW.favorite
                         WHERE id_user = %(id_user)s
                         ORDER BY added_at DESC;
                        """,
                        {"id_user": id_user},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding favorites of user {id_user}: {e}")
            raise

        return [
            Favorite(
                id=row["id_favorite"],
                user_id=row["id_user"],
                neo_id=row["id_neo"],
                added_at=row["added_at"],
            )
            for row in rows
        ]

    @log
    def exists(self, id_user: int, id_neo: int) -> bool:
        """
        Checks whether a NEO is already in a user's favorites.

        Args:
            id_user (int): The id of the user.
            id_neo (int): The id of the NEO.

        Returns:
            bool: True if the NEO is already a favorite of the user.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT 1
                          FROM NEOW.favorite
                         WHERE id_user = %(id_user)s
                           AND id_neo = %(id_neo)s;
                        """,
                        {"id_user": id_user, "id_neo": id_neo},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error checking favorite (user {id_user}, neo {id_neo}): {e}")
            raise

        return res is not None

    @log
    def delete(self, favorite: Favorite) -> bool:
        """
        Removes a NEO from a user's favorites.
        Its distance history is deleted first, since it references the favorite.

        Args:
            favorite (Favorite): The favorite to delete.

        Returns:
            bool: True if the favorite was deleted, False if it did not exist.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM NEOW.distance_history WHERE id_favorite = %(id_favorite)s;",
                        {"id_favorite": favorite.id},
                    )
                    cursor.execute(
                        "DELETE FROM NEOW.favorite WHERE id_favorite = %(id_favorite)s;",
                        {"id_favorite": favorite.id},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(f"Error deleting favorite {favorite.id}: {e}")
            raise

        return res > 0
