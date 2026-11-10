"""Service managing the connection history: recording and searching the logins."""

from datetime import datetime

from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class ConnectionHistoryService:
    """Service that handles the business logic related to connections (creation, search)."""

    @log
    def create(self, id_user: int) -> Connection | None:
        """Records a new connection of a user, dated now.

        Errors are logged and never raised: the history is secondary information,
        and a failure to record it must not break the caller (e.g. a login).

        Args:
            id_user (int): The id of the user who logged in.

        Returns:
            Connection | None: The created connection, or None if it could not be saved.
        """
        try:
            connection = Connection(id_user=id_user, login_at=datetime.now())
            if LoginHistoryDao().create(connection):
                logger.info("Connection history created for user %s", id_user)
                return connection
            logger.warning("Failed to create connection for user %s", id_user)
        # Voluntarily broad: whatever the failure, the caller must keep working
        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.error("Error creating the connection of user %s: %s", id_user, error)
        return None

    @log
    def find_by_id_user(self, id_user: int) -> list[Connection]:
        """Finds all the connections of a user.

        Args:
            id_user (int): The id of the user.

        Returns:
            list[Connection]: The connections of this user (empty list if none).
        """
        return LoginHistoryDao().find_by_id_user(id_user)

    @log
    def find_all(self) -> list[Connection]:
        """Finds the connections of all users.

        Returns:
            list[Connection]: All the connections (empty list if none).
        """
        return LoginHistoryDao().find_all()
