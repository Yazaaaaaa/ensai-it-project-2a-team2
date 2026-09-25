from business_object.notification import Notification
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class NotificationDao(metaclass=Singleton):
    """Class containing methods to access notifications in the database."""

    @log
    def create(self, notification: Notification) -> bool:
        """
        Inserts a new notification (created when one of the user's alerts is triggered).

        Args:
            notification (Notification): The notification to persist.

        Returns:
            bool: True if the insertion is successful, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO NEOW.notification (id_user, id_alert, message)
                        VALUES (%(id_user)s, %(id_alert)s, %(message)s)
                        RETURNING id_notification, sent_at;
                        """,
                        {
                            "id_user": notification.id_user,
                            "id_alert": notification.id_alert,
                            "message": notification.message,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating notification for user {notification.id_user}: {e}")
            raise

        created = False
        if res:
            notification.id_notification = res["id_notification"]
            notification.sent_at = res["sent_at"]
            created = True

        return created

    @log
    def find_by_id(self, id_notification: int) -> Notification | None:
        """
        Retrieves a notification from its id.

        Args:
            id_notification (int): The id of the notification.

        Returns:
            Notification: The notification if found, otherwise None.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM NEOW.notification
                         WHERE id_notification = %(id_notification)s;
                        """,
                        {"id_notification": id_notification},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error finding notification {id_notification}: {e}")
            raise

        if not res:
            return None

        return Notification(
            id_notification=res["id_notification"],
            id_user=res["id_user"],
            id_alert=res["id_alert"],
            message=res["message"],
            sent_at=res["sent_at"],
        )

    @log
    def find_all_by_user(self, id_user: int) -> list[Notification]:
        """
        Returns all the notifications of a user, the most recent first.
        Used to display the notifications when the user logs in.

        Args:
            id_user (int): The id of the user.

        Returns:
            list[Notification]: The user's notifications (empty list if none).
        """
        rows = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM NEOW.notification
                         WHERE id_user = %(id_user)s
                         ORDER BY sent_at DESC;
                        """,
                        {"id_user": id_user},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding notifications of user {id_user}: {e}")
            raise

        return [
            Notification(
                id_notification=row["id_notification"],
                id_user=row["id_user"],
                id_alert=row["id_alert"],
                message=row["message"],
                sent_at=row["sent_at"],
            )
            for row in rows
        ]

    @log
    def delete(self, notification: Notification) -> bool:
        """
        Deletes a notification (for example once the user has dismissed it).

        Args:
            notification (Notification): The notification to delete.

        Returns:
            bool: True if the notification was deleted, False if it did not exist.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM NEOW.notification WHERE id_notification = %(id)s;",
                        {"id": notification.id_notification},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(f"Error deleting notification {notification.id_notification}: {e}")
            raise

        return res > 0
