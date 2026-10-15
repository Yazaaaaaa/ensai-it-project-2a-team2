from datetime import datetime

from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao
from utils.log_utils import log


class ConnectionHistoryService:
    """Service that handles business logic related to connections (creation, search)."""

    @log
    def create(self, id_user: int) -> Connection:
        """Creates a new connection"""
        new_connection = Connection(
            id_user=id_user,
            timestamp=datetime.now()
        )
        return new_connection if LoginHistoryDao().create(new_connection) else None

    @log
    def find_by_id_user(self, id_user: int) -> list[Connection]:
        """Finds all connections of a user by his id"""
        return LoginHistoryDao().find_by_id_user(id_user)

    @log
    def find_all(self) -> list[Connection]:
        """Finds all connections"""
        return LoginHistoryDao().find_all()
