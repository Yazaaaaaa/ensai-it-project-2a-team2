from datetime import datetime


class User:
    def __init__(
        self,
        email: str,
        password_hash: str,
        role_user: str,
        id_user: int | None = None,
        created_at: datetime | None = None,
        token: str | None = None,
        is_banned: bool = False
    ):
        self.id_user = id_user
        self.email = email
        self.password_hash = password_hash
        self.role_user = role_user
        self.created_at = created_at
        self.token = token
        self.is_banned = is_banned