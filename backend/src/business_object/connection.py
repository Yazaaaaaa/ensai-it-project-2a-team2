from datetime import datetime


class Connection:
    """Business object representing connections at the app."""

    def __init__(self, id_user: int, id_login: int, login_at: datetime):
        self.id_user = id_user
        self.id_login = None
        self.login_at = login_at if login_at else datatime().now
