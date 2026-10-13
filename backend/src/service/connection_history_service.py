from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao


class ConnectionHistoryService:
    """Service that handles business logic related to connections (creation, search, etc.)."""

    @log
    def create(self, login: Connection) -> Player:
        """Creates a new connection"""
        new_connection = Connection(
            id_user=id_user,
            id_login=id_login,
            timestamp=datetime.now()
        )
        return new_connection if LoginHistoryDao().create(new_connection) else None

    @log
    def find_by_id_user(self, id_user: int) -> list[Connection:
        """Finds all connections of a user by his id"""
        return LoginHistoryDao().find_by_id_user(id_user)
  
    @log
    def find_all(self) -> list[Connection]:
        """Finds all connections"""
        return LoginHistoryDao().find_all()

