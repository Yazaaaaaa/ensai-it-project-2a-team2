from datetime import datetime


class Connection:
    """Business object representing connections at the app."""

    def __init__(self, id_user: int, id_login: int, timestamp: datetime):
        self.id_user = id_user,
        self.id_login = id_login
        self.timestamp = timestamp
