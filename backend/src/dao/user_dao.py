import logging

from utils.log_utils import log

from business_object.user import User
from dao.db_connection import DBConnection
from utils.singleton import Singleton


class UserDao(metaclass=Singleton):
    """Accès aux données de la table neow.users"""

    @log
    def create(self, user: User) -> bool:
            """Insère un utilisateur et renseigne son id et sa date de création."""
            try:
                with DBConnection().connection as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO neow.users (email, password_hash, role_user, token) "
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
            except Exception as e:
                print(f"Erreur SQL create user : {e}")
                return False

            created = False
            if res:
                user.id = res["id_user"] 
                user.created_at = res["created_at"]
                created = True

            return created

    @log
    def find_by_id(self, id: int) -> User | None:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM neow.users WHERE id = %(id)s;",
                    {"id": id},
                )
                res = cursor.fetchone()
        return self._to_user(res)

    @log
    def find_by_email(self, email: str) -> User | None:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM neow.users WHERE email = %(email)s;",
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
                        "SELECT id_user, email, password_hash, role_user, created_at, token "
                        "FROM neow.users WHERE token = %(token)s;",
                        {"token": token},
                    )
                    row = cursor.fetchone()
        except Exception as e:
            print(f"Erreur find_by_token : {e}")
            return None

        if row:
            return User(
                id=row["id_user"],
                email=row["email"],
                password_hash=row["password_hash"],
                role_user=row["role_user"],
                created_at=row["created_at"],
                token=row["token"],
            )
        return None

    @log
    def find_all(self) -> list[User]:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM neow.users ORDER BY id;")
                res = cursor.fetchall()
        return [self._to_user(row) for row in res]

    @log
    def update(self, user: User) -> bool:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE neow.users "
                    "SET email = %(email)s, password_hash = %(password_hash)s, role = %(role)s "
                    "WHERE id = %(id_user)s;",
                    {
                        "id_user": user.id_user,
                        "email": user.email,
                        "password_hash": user.password_hash,
                        "role_user": user.role_user,
                    },
                )
                return cursor.rowcount == 1

    @log
    def delete(self, user: User) -> bool:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM neow.users WHERE id_user = %(id_user)s;",
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
        )
