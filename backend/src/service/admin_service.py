"""Service gathering the actions reserved to administrators."""

import subprocess
import sys
import threading
from pathlib import Path

from business_object.connection import Connection
from business_object.user import User
from dao.user_dao import UserDao
from service.connection_history_service import ConnectionHistoryService
from utils.log_utils import get_logger

logger = get_logger(__name__)

ADMIN_ROLE = "admin"

# Module run in a separate process to reload the NASA data
IMPORT_MODULE = "utils.weekly_data"

# Folder backend/src/ (parent of service/). The import runs from there,
# so that "utils.weekly_data" can be found as a module.
SRC_DIR = Path(__file__).resolve().parents[1]

# Maximum duration of the import (seconds) and number of output characters kept
DEFAULT_IMPORT_TIMEOUT = 3600
OUTPUT_TAIL_CHARS = 5000


class AdminService:
    """Actions reserved to administrators: ban, data import, connection history."""

    # Shared by all instances: only one import can run at a time
    _import_lock = threading.Lock()

    def __init__(
        self,
        user_dao: UserDao | None = None,
        connection_service: ConnectionHistoryService | None = None,
    ):
        """Creates the service; the dependencies can be injected (e.g. mocks in tests)."""
        self.user_dao = user_dao or UserDao()
        self.connection_service = connection_service or ConnectionHistoryService()

    # ------------------------------------------------------------ ban

    def ban_user(self, admin: User, id_user: int) -> bool:
        """Bans a user: he can no longer log in and his current session is closed.

        Args:
            admin (User): the user performing the action.
            id_user (int): the id of the user to ban.

        Returns:
            bool: True if the ban was saved.

        Raises:
            PermissionError: the caller is not an admin.
            ValueError: unknown user, self-ban, or target is an admin.
        """
        self._require_admin(admin)
        if admin.id_user == id_user:
            raise ValueError("An admin cannot ban himself")

        target = self.user_dao.find_by_id(id_user)
        if target is None:
            raise ValueError("User not found")
        if target.role_user == ADMIN_ROLE:
            raise ValueError("An admin cannot be banned")

        target.is_banned = True
        target.token = None  # removing the token closes the current session
        banned = self.user_dao.update(target)
        if banned:
            logger.info("User %s banned by admin %s", id_user, admin.id_user)
        return banned

    # ------------------------------------------------------------ data import

    def run_data_import(self, admin: User, timeout: int = DEFAULT_IMPORT_TIMEOUT) -> dict:
        """Runs the data import (IMPORT_MODULE) in a separate process.

        Args:
            admin (User): the user performing the action.
            timeout (int): maximum duration of the import, in seconds.

        Returns:
            dict: success, returncode, stdout and stderr (last characters only).

        Raises:
            PermissionError: the caller is not an admin.
            RuntimeError: an import is already running.
        """
        self._require_admin(admin)
        # Non-blocking: refuse immediately instead of waiting for the running import
        if not self._import_lock.acquire(blocking=False):
            raise RuntimeError("An import is already running")

        try:
            logger.info("Data import started by admin %s", admin.id_user)
            result = subprocess.run(
                [sys.executable, "-m", IMPORT_MODULE],
                cwd=SRC_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # a failure is reported in the result, not raised
            )
        except subprocess.TimeoutExpired:
            logger.error("Data import timed out after %ss", timeout)
            return {
                "success": False,
                "returncode": None,
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
            }
        finally:
            # Always released, even on timeout or unexpected error
            self._import_lock.release()

        success = result.returncode == 0
        if success:
            logger.info("Data import finished successfully")
        else:
            logger.error("Data import failed (code %s)", result.returncode)

        return {
            "success": success,
            "returncode": result.returncode,
            "stdout": result.stdout[-OUTPUT_TAIL_CHARS:],
            "stderr": result.stderr[-OUTPUT_TAIL_CHARS:],
        }

    @classmethod
    def is_import_running(cls) -> bool:
        """Tells whether a data import is currently running."""
        return cls._import_lock.locked()

    # ------------------------------------------------------------ connection history

    def get_connection_history(
        self, admin: User, id_user: int | None = None
    ) -> list[Connection]:
        """Returns the connection history, of one user or of all users.

        Args:
            admin (User): the user performing the action.
            id_user (int | None): the user to look at; None for all users.

        Returns:
            list[Connection]: the connections found.

        Raises:
            PermissionError: the caller is not an admin.
            ValueError: unknown user.
        """
        self._require_admin(admin)
        if id_user is None:
            return self.connection_service.find_all()
        if self.user_dao.find_by_id(id_user) is None:
            raise ValueError("User not found")
        return self.connection_service.find_by_id_user(id_user)

    # ------------------------------------------------------------ helpers

    @staticmethod
    def _require_admin(admin: User | None) -> None:
        """Checks that the caller is an admin.

        Raises:
            PermissionError: the caller is missing or is not an admin.
        """
        if admin is None or admin.role_user != ADMIN_ROLE:
            raise PermissionError("Admin rights required")
