from business_object.connection import Connection
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

# from business_object.user import User


logger = get_logger(__name__)


class LoginHistoryDao(metaclass=Singleton):
    """Class containing methods to access the login history of users by the login_history table"""
    @log
    def create(self, login: Connection) -> bool:
        """
        Inserts a new connection record.
        When a user log in the app, a new connection record is create to monitor date
        of each connection.
        Args:
            user: informations about the user logging in
        Returns:
           bool: True if insertion is successful, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO NEOW.login_history(id_user) "
                        "VALUES (%(id_user)s) "
                        "RETURNING id_login, login_at;",
                        {
                            "id_user": login.id_user,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating login history: {e}")
            raise

        created = False
        if res:
            login.id_login = res["id_login"]
            login.timestamp = res["login_at"]
            created = True

        return created

    @log
    def find_by_id_user(self, id_user: int) -> list[Connection] | None:
        """
        Returns the connection history of a user by his id.
        Args:
            id_user (int): The id of the user
        Returns:
            list(Connection): List of connections made by the user. If there's no connection, None.
        """
        rows = []

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                        FROM NEOW.login_history
                        WHERE id_user = %(id_user)s
                        ORDER BY timestamp DESC;
                        """,
                        {"id_user": id_user},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding connections for user {id_user}: {e}")
            raise

        if not rows:
            return None

        connections = []
        for row in rows:

            connections.append(
                Connection(
                    id_login=row["id_login"],
                    id_user=row[id_user],
                    timestamp=row["timestamp"],
                )
            )

        return connections

    @log
    def find_all(self) -> list[Connection] | None:
        """
        Returns the connection history of all users.
        Returns:
            list(Connection): List of connections made. If there's no connection, None.
        """
        rows = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                        FROM NEOW.login_history
                        ORDER BY login_at DESC;
                        """
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding all connections: {e}")
            raise

        if not rows:
            return None

        connections = []
        for row in rows:

            connections.append(
                Connection(
                    id_login=row["id_login"],
                    id_user=row["id_user"],
                    timestamp=row["timestamp"],
                )
            )

        return connections
