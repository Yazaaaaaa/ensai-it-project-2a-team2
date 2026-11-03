import logging
import subprocess
import sys
import threading
from pathlib import Path

from business_object.user import User
from dao.user_dao import UserDao

logger = logging.getLogger(__name__)

ADMIN_ROLE = "admin"
IMPORT_MODULE = "utils.import_all_data"
# admin_service.py est dans backend/src/service/ -> backend/src/ est le dossier parent
SRC_DIR = Path(__file__).resolve().parents[1]
OUTPUT_TAIL_CHARS = 5000


class AdminService:
    """Actions réservées aux administrateurs."""

    _import_lock = threading.Lock()

    def __init__(self, user_dao: UserDao | None = None):
        self.user_dao = user_dao or UserDao()

    # ---------------------------------------------------------------- ban

    def ban_user(self, admin: User, id_user: int) -> bool:
        """
        Bans a user: he can no longer log in and his current session is closed.

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
        target.token = None  # ferme la session en cours
        banned = self.user_dao.update(target)
        if banned:
            logger.info(f"User {id_user} banned by admin {admin.id_user}")
        return banned

    # ------------------------------------------------------------- import

    def run_data_import(self, admin: User, timeout: int = 3600) -> dict:
        """
        Runs utils.import_all_data in a separate process.

        Returns:
            dict: success, returncode, stdout and stderr (last characters only).

        Raises:
            PermissionError: the caller is not an admin.
            RuntimeError: an import is already running.
        """
        self._require_admin(admin)
        if not self._import_lock.acquire(blocking=False):
            raise RuntimeError("An import is already running")

        try:
            logger.info(f"Data import started by admin {admin.id_user}")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", IMPORT_MODULE],
                    cwd=SRC_DIR,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                logger.error(f"Data import timed out after {timeout}s")
                return {"success": False, "returncode": None, "stdout": "",
                        "stderr": f"Timeout after {timeout}s"}

            success = result.returncode == 0
            if success:
                logger.info("Data import finished successfully")
            else:
                logger.error(f"Data import failed (code {result.returncode})")
            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout[-OUTPUT_TAIL_CHARS:],
                "stderr": result.stderr[-OUTPUT_TAIL_CHARS:],
            }
        finally:
            self._import_lock.release()

    @classmethod
    def is_import_running(cls) -> bool:
        return cls._import_lock.locked()
    # ------------------------------------------------------------ helpers

    @staticmethod
    def _require_admin(admin: User | None) -> None:
        if admin is None or admin.role_user != ADMIN_ROLE:
            raise PermissionError("Admin rights required")