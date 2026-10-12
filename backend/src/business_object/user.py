from datetime import datetime


class User:
    def __init__(
        self, id: int, email: str, password_hash: str, role: str, created_at=datetime.now()
    ):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
