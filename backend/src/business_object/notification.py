from datetime import datetime


class Notification:
    """Business object representing a notification sent to a user when an alert is triggered."""

    def __init__(
        self,
        id_user: int,
        id_alert: int,
        message: str,
        sent_at: datetime = None,
        id_notification: int = None,
    ):
        self.id_notification = id_notification
        self.id_user = id_user
        self.id_alert = id_alert
        self.message = message
        self.sent_at = sent_at

    def __str__(self):
        return f"Notification({self.id_notification}: user {self.id_user}, {self.message})"
