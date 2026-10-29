from datetime import datetime


class User:
    def __init__(
        self, id_user: int, email: str, password_hash: str, role_user: str, created_at: datetime, token: str
    ):
        self.id_user = id
        self.email = email
        self.password_hash = password_hash
        self.role_user = role_user
        self.token = None
