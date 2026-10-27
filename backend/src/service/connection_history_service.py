from datetime import datetime

from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class ConnectionHistoryService:
    """Service that handles business logic related to connections (creation, search)."""

    @log
    def create(self, id_user: int) -> Connection | None:
        """Creates a new connection history entry.
        Args:
            id_user: The user ID to record the connection
        Returns:
            Connection: The created connection object, or None
        """
        try:
            new_connection = Connection(id_user=id_user)
            if LoginHistoryDao().create(new_connection):
                logger.info(f"Connection history created for user {id_user}")
                return new_connection
            else:
                logger.warning(f"Failed to create connection for user {id_user}")
                return None
        except Exception as e:
            logger.error(f"Error in ConnectionHistoryService.create {e}")
            return None

    @log
    def find_by_id_user(self, id_user: int) -> list[Connection]:
        """Finds all connections of a user by his id"""
        return LoginHistoryDao().find_by_id_user(id_user)

    @log
    def find_all(self) -> list[Connection]:
        """Finds all connections"""
        return LoginHistoryDao().find_all()
