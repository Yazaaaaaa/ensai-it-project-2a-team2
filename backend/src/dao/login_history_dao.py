from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton


class LoginHistoryDao(metaclass=Singleton):
    """Class containing methods to access the login history of users by the login_history table"""
    @log
    def create(self, user) -> bool:
        """
        Inserts a new connection record.
        When a user log in the app, a new connection record is create to monitor date and ip adress
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
                        "INSERT INTO NEOW.login_history(id_user, ip_address) "
                        "VALUES (%(id_user)s, %(ip_address)s) "
                        "RETURNING id_login;",
                        {
                            "id_user": user.id_user,
                            "ip_address": game.winner.id_player if game.winner else None,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            raise

        created = False
        if res:
            game.id_game = res["id_game"]
            created = True

        return created

    @log
    def find_by_id_user(self, id_user: int) -> list() | None:
        """
        Retrieves the connection history of a user by his id.
        Args:
            id_user (int): The id of the user
        Returns:
            list: List of connections made by the user. If there's no connection, None.
        """
        pass
