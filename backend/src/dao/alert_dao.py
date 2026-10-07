from business_object.alert import Alert
from dao.db_connection import DBConnection
from utils.log_utils import log
from utils.singleton import Singleton


class AlertDao(metaclass=Singleton):
    """Class containing methods to access alerts in the database."""

    @log
    def create(self, alert: Alert) -> bool:
        """
        Creates an alert for a user on a NEO.

        Args:
            alert (Alert): The alert to persist (user_id, neo_id, threshold_km, is_active).

        Returns:
            bool: True if the insertion is successful, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO NEOW.alert (id_user, id_neo, threshold_km, is_active)
                        VALUES (%(id_user)s, %(id_neo)s, %(threshold_km)s, %(is_active)s)
                        RETURNING id_alert, created_at;
                        """,
                        {
                            "id_user": alert.user_id,
                            "id_neo": alert.neo_id,
                            "threshold_km": alert.threshold_km,
                            "is_active": alert.is_active,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating alert {alert}: {e}")
            raise

        created = False
        if res:
            alert.id = res["id_alert"]
            alert.created_at = res["created_at"]
            created = True

        return created

    @log
    def get_by_userid(self, user_id: int) -> list[Alert]:
        """
        Retrieves all alerts of a user.

        Args:
            user_id (int): The id of the user.

        Returns:
            list[Alert]: The user's alerts (empty list if none).
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id_alert, id_user, id_neo, threshold_km, is_active, created_at
                        FROM NEOW.alert
                        WHERE id_user = %(id_user)s
                        ORDER BY created_at DESC;
                        """,
                        {"id_user": user_id},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error retrieving alerts for user {user_id}: {e}")
            raise

        return [
            Alert(
                id=row["id_alert"],
                user_id=row["id_user"],
                neo_id=row["id_neo"],
                threshold_km=row["threshold_km"],
                is_active=row["is_active"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @log
    def update(self, alert: Alert) -> bool:
        """
        Updates an existing alert (threshold and activation status).

        Args:
            alert (Alert): The alert to update (its id must be set).

        Returns:
            bool: True if an alert was updated, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE NEOW.alert
                        SET threshold_km = %(threshold_km)s,
                            is_active = %(is_active)s
                        WHERE id_alert = %(id_alert)s
                        RETURNING id_alert;
                        """,
                        {
                            "threshold_km": alert.threshold_km,
                            "is_active": alert.is_active,
                            "id_alert": alert.id,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error updating alert {alert}: {e}")
            raise

        return res is not None

    @log
    def delete(self, alert_id: int) -> bool:
        """
        Deletes an alert.

        Args:
            alert_id (int): The id of the alert to delete.

        Returns:
            bool: True if an alert was deleted, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM NEOW.alert
                        WHERE id_alert = %(id_alert)s
                        RETURNING id_alert;
                        """,
                        {"id_alert": alert_id},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error deleting alert {alert_id}: {e}")
            raise

        return res is not None
