import logging

from business_object.user import User
from dao.db_connection import DBConnection
from utils.log_utils import log
from utils.singleton import Singleton

logger = logging.getLogger(__name__)


class UserDao(metaclass=Singleton):
    """Accès aux données de la table users"""

    @log
    def create(self, user: User) -> bool:
        """Insère un utilisateur et renseigne son id et sa date de création."""
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
            logger.exception("Erreur SQL create user")
            return False

        if res:
            user.id_user = res["id_user"]
            user.created_at = res["created_at"]
            return True
        return False

    @log
    def find_by_id(self, id_user: int) -> User | None:
        """Trouve un utilisateur à partir de son id."""
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
        """Trouve un utilisateur à partir de son email."""
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
        """Trouve un utilisateur à partir de son token."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_user, email, password_hash, role_user, created_at, token, is_banned"
                        "FROM users WHERE token = %(token)s;",
                        {"token": token},
                    )
                    res = cursor.fetchone()
        except Exception:
            logger.exception("Erreur SQL find_by_token")
            return None
        return self._to_user(res)

    @log
    def find_all(self) -> list[User]:
        """Renvoie tous les utilisateurs."""
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
        """Met à jour email, mot de passe, rôle et token d'un utilisateur."""
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
                        "is_banned": user.is_banned
                    },
                )
                return cursor.rowcount == 1

    @log
    def delete(self, user: User) -> bool:
        """Supprime un utilisateur."""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE id_user = %(id_user)s;",
                    {"id_user": user.id_user},
                )
                return cursor.rowcount > 0

    @staticmethod
    def _to_user(row: dict | None) -> User | None:
        if row is None:
            return None
        return User(
            id_user=row["id_user"],
            email=row["email"],
            password_hash=row["password_hash"],
            role_user=row["role_user"],
            created_at=row["created_at"],
            token=row["token"],
            is_banned=row["is_banned"]
        )