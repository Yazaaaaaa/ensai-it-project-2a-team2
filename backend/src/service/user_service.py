"""Service managing user accounts: creation, login, logout and token authentication."""

import hashlib
import hmac
import secrets

from business_object.user import User
from dao.user_dao import UserDao
from utils.log_utils import get_logger

logger = get_logger(__name__)

# Number of PBKDF2 rounds: the higher, the slower a brute-force attack.
# 600,000 is the OWASP recommendation for PBKDF2-HMAC-SHA256.
PBKDF2_ITERATIONS = 600_000

# Minimum number of characters of a password
MIN_PASSWORD_LENGTH = 8

# Size in bytes of the random salt (unique per password) and of the session token
SALT_BYTES = 16
TOKEN_BYTES = 32


class UserService:
    """Account creation, login, logout and authentication by token."""

    def __init__(self, user_dao: UserDao | None = None):
        """Creates the service; the DAO can be injected (e.g. a mock in tests)."""
        self.user_dao = user_dao or UserDao()

    # ------------------------------------------------------------ account

    def create_account(self, email: str, password: str, role_user: str = "user") -> User:
        """Creates an account and saves the user in the database.

        Args:
            email (str): the email, used as login (stored in lower case).
            password (str): the clear password, stored only as a salted hash.
            role_user (str): the role of the new user.

        Returns:
            User: the created user.

        Raises:
            ValueError: invalid email, password too short or email already used.
            RuntimeError: the insertion failed.
        """
        email = self._normalize_email(email)
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

        logger.info("Account created for user %s", user.id_user)
        return user

    # ------------------------------------------------------------ session

    def login(self, email: str, password: str) -> User | None:
        """Checks the credentials and opens a session by generating a new token.

        The same result (None) is returned for an unknown email and a wrong password,
        so that an attacker cannot find out which emails have an account.

        Args:
            email (str): the email of the user.
            password (str): the clear password to check.

        Returns:
            User | None: the user with a fresh token, None if the login is refused
                (invalid credentials, banned user or token not saved).
        """
        user = self.user_dao.find_by_email(self._normalize_email(email))
        if user is None or not self._verify_password(password, user.password_hash):
            logger.warning("Failed login attempt")
            return None

        # Checked after the password: a banned status is not revealed without it
        if user.is_banned:
            logger.warning("Login refused for banned user %s", user.id_user)
            return None

        user.token = secrets.token_urlsafe(TOKEN_BYTES)
        if not self.user_dao.update(user):
            logger.error("Could not save the token of user %s", user.id_user)
            return None
        return user

    def logout(self, token: str) -> bool:
        """Closes the session associated with a token.

        Args:
            token (str): the session token.

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

    def authenticate(self, token: str) -> User | None:
        """Finds the user owning a session token.

        Args:
            token (str): the session token.

        Returns:
            User | None: the user, None if the token is invalid or the user is banned.
        """
        if not token:
            return None
        user = self.user_dao.find_by_token(token)
        if user is None or user.is_banned:
            return None
        return user

    # ------------------------------------------------------------ helpers

    @staticmethod
    def _normalize_email(email: str) -> str:
        """Removes surrounding spaces and lowers the case, so emails compare reliably."""
        return email.strip().lower()

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hashes a password with PBKDF2-HMAC-SHA256 and a random salt.

        Returns:
            str: "pbkdf2_sha256$<iterations>$<salt in hex>$<hash in hex>". The salt and the
                iteration count are kept in the string so that the password can be checked.
        """
        salt = secrets.token_bytes(SALT_BYTES)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
        return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verify_password(password: str, stored_hash: str | None) -> bool:
        """Checks a clear password against a hash made by _hash_password.

        Returns:
            bool: True if the password matches, False if it does not or if the stored
                hash is missing or malformed (e.g. a clear text password in test data).
        """
        try:
            _, iterations, salt_hex, hash_hex = stored_hash.split("$")
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
            )
        except (ValueError, AttributeError):
            return False
        # Constant-time comparison: its duration does not reveal how many characters match
        return hmac.compare_digest(digest.hex(), hash_hex)
