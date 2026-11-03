import hashlib
import hmac
import logging
import secrets

from business_object.user import User
from dao.user_dao import UserDao

logger = logging.getLogger(__name__)

PBKDF2_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 8


class UserService:
    """Account creation, login and logout."""

    def __init__(self, user_dao: UserDao | None = None):
        self.user_dao = user_dao or UserDao()

    # ------------------------------------------------------------ account

    def create_account(self, email: str, password: str, role_user: str = "user") -> User:
        """
        Creates an account and saves the user in the database.

        Raises:
            ValueError: invalid email, password too short or email already used.
            RuntimeError: the insertion failed.
        """
        email = email.strip().lower()
        if "@" not in email:
            raise ValueError("Invalid email address")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must contain at least {MIN_PASSWORD_LENGTH} characters")
        if self.user_dao.find_by_email(email) is not None:
            raise ValueError("Email already used")

        user = User(
            id_user=None,
            email=email,
            password_hash=self._hash_password(password),
            role_user=role_user,
            token=None,
            created_at=None,
        )
        if not self.user_dao.create(user):
            raise RuntimeError("Account creation failed")

        logger.info(f"Account created for user {user.id_user}")
        return user

    # -------------------------------------------------------------- login

    def login(self, email: str, password: str) -> User | None:
        """
        Checks the credentials and opens a session by generating a new token.

        Returns:
            User | None: the user with a fresh token, None if the credentials are invalid.
        """
        user = self.user_dao.find_by_email(email.strip().lower())
        if user is None or not self._verify_password(password, user.password_hash):
            logger.warning("Failed login attempt")
            return None

        if user.is_banned:
            logger.warning(f"Login refused for banned user {user.id_user}")
            return None

        user.token = secrets.token_urlsafe(32)
        if not self.user_dao.update(user):
            logger.error(f"Could not save the token of user {user.id_user}")
            return None
        return user

    # ------------------------------------------------------------- logout

    def logout(self, token: str) -> bool:
        """
        Closes the session associated with a token.

        Returns:
            bool: True if a session was closed, False if the token is unknown.
        """
        if not token:
            return False
        user = self.user_dao.find_by_token(token)
        if user is None:
            return False

        user.token = None
        return self.user_dao.update(user)

    # ------------------------------------------------------------ helpers

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
        return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        try:
            _, iterations, salt_hex, hash_hex = stored_hash.split("$")
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
            )
        except (ValueError, AttributeError):
            return False
        return hmac.compare_digest(digest.hex(), hash_hex)