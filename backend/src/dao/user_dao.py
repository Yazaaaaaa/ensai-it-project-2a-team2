import logging

from business_object.user import User
from dao.db_connection import DBConnection
from utils.log_utils import log
from utils.singleton import Singleton

logger = logging.getLogger(__name__)


class UserDao(metaclass=Singleton):
    """Class containing methods to access users in the database."""

    @log
    def create(self, user: User) -> bool:
        """
        Inserts a new user and sets its generated ID and creation timestamp.

        Args:
            user (User): The user object to persist.

        Returns:
            bool: True if the insertion is successful, False otherwise.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (email, password_hash, role_user, token) "
                        "VALUES (%(email)s, %(password_hash)s, %(role_user)s, %(token)s) "
                        "RETURNING id_user, created_at;",
                        {
                            "email": user.email,
                            "password_hash": user.password_hash,
                            "role_user": user.role_user,
                            "token": user.token,
                        },
                    )
                    res = cursor.fetchone()
        except Exception:
            logger.exception("SQL error while creating user")
            return False

        if res:
            user.id_user = res["id_user"]
            user.created_at = res["created_at"]
            return True
        return False

    @log
    def find_by_id(self, id_user: int) -> User | None:
        """
        Retrieves a user by its primary key ID.

        Args:
            id_user (int): The ID of the user to find.

        Returns:
            User | None: The matching User object if found, otherwise None.
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id_user, email, password_hash, role_user, created_at, token, is_banned "
                    "FROM users WHERE id_user = %(id_user)s;",
                    {"id_user": id_user},
                )
                res = cursor.fetchone()
        return self._to_user(res)

    @log
    def find_by_email(self, email: str) -> User | None:
        """
        Retrieves a user by its email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User | None: The matching User object if found, otherwise None.
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id_user, email, password_hash, role_user, created_at, token, is_banned "
                    "FROM users WHERE email = %(email)s;",
                    {"email": email},
                )
                res = cursor.fetchone()
        return self._to_user(res)

    @log
    def find_by_token(self, token: str) -> User | None:
        """
        Retrieves a user by its authentication token.

        Args:
            token (str): The token associated with the user.

        Returns:
            User | None: The matching User object if found, otherwise None.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_user, email, password_hash, role_user, created_at, token,"
                        "is_banned "
                        "FROM users WHERE token = %(token)s;",
                        {"token": token},
                    )
                    res = cursor.fetchone()
        except Exception:
            logger.exception("SQL error in find_by_token")
            return None
        return self._to_user(res)

    @log
    def find_all(self) -> list[User]:
        """
        Retrieves all users ordered by their ID.

        Returns:
            list[User]: List of all User objects.
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id_user, email, password_hash, role_user, created_at, token, is_banned "
                    "FROM users ORDER BY id_user;"
                )
                res = cursor.fetchall()
        return [self._to_user(row) for row in res]

    @log
    def update(self, user: User) -> bool:
        """
        Updates a user's email, password hash, role, token, and ban status.

        Args:
            user (User): The user object containing updated fields and its id_user.

        Returns:
            bool: True if exactly one row was updated, False otherwise.
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users "
                    "SET email = %(email)s, password_hash = %(password_hash)s, "
                    "role_user = %(role_user)s, token = %(token)s, is_banned = %(is_banned)s "
                    "WHERE id_user = %(id_user)s;",
                    {
                        "id_user": user.id_user,
                        "email": user.email,
                        "password_hash": user.password_hash,
                        "role_user": user.role_user,
                        "token": user.token,
                        "is_banned": user.is_banned,
                    },
                )
                # Ensure a single target user row was modified
                return cursor.rowcount == 1

    @log
    def delete(self, user: User) -> bool:
        """
        Deletes a user from the database.

        Args:
            user (User): The user object to delete (uses user.id_user).

        Returns:
            bool: True if at least one row was deleted, False otherwise.
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE id_user = %(id_user)s;",
                    {"id_user": user.id_user},
                )
                return cursor.rowcount > 0

    @staticmethod
    def _to_user(row: dict | None) -> User | None:
        """
        Converts a database row dictionary into a User business object.

        Args:
            row (dict | None): Database row returned by the cursor.

        Returns:
            User | None: Instantiated User object, or None if row is None.
        """
        if row is None:
            return None
        return User(
            id_user=row["id_user"],
            email=row["email"],
            password_hash=row["password_hash"],
            role_user=row["role_user"],
            created_at=row["created_at"],
            token=row["token"],
            is_banned=row["is_banned"],
        )