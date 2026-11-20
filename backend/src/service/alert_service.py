from datetime import date

from fastapi import HTTPException

from business_object.alert import Alert
from business_object.close_approach import CloseApproach
from business_object.neo import Neo
from dao.alert_dao import AlertDao
from dao.close_approach_dao import CloseApproachDao
from dao.neo_dao import NeoDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)

UPDATABLE_FIELDS = ("threshold_km", "threshold_size", "is_active")

EARTH = "Earth"


class AlertService:
    """Service that manages the alerts of the users on the NEOs they watch."""

    @log
    def add(
        self,
        id_user: int,
        id_neo: int | None,
        threshold_km: float,
        threshold_size: float | None = None,
        is_active: bool = True,
    ) -> tuple[Alert, Neo | None]:
        """
        Creates an alert for a user, on one NEO or on any NEO (id_neo=None).

        Args:
            id_user (int): ID of the user creating the alert.
            id_neo (int | None): ID of the target NEO, or None for a global alert.
            threshold_km (float): Maximum miss distance threshold in kilometers.
            threshold_size (float | None): Minimum NEO size threshold in meters, if any.
            is_active (bool): Whether the alert starts active.

        Returns:
            tuple[Alert, Neo | None]: The created Alert and the watched Neo (or None).

        Raises:
            HTTPException: 404 if the NEO does not exist, 409 if the user already watches it,
                or 500 if persistence fails.
        """
        dao = AlertDao()
        neo = None
        if id_neo is not None:
            neo = NeoDao().find_by_id_neo(id_neo)
            if neo is None:
                raise HTTPException(status_code=404, detail="NEO not found")
            # Prevent duplicate per-NEO alerts for the same user
            if any(a.neo_id == id_neo for a in dao.get_by_userid(id_user)):
                raise HTTPException(status_code=409, detail="This NEO already has an alert")

        alert = Alert(
            user_id=id_user,
            neo_id=id_neo,
            threshold_km=threshold_km,
            threshold_size=threshold_size,
            is_active=is_active,
        )
        if not dao.create(alert):
            raise HTTPException(status_code=500, detail="The alert could not be created")

        return alert, neo

    @log
    def list_alerts(self, id_user: int) -> list[tuple[Alert, Neo | None]]:
        """
        Lists the alerts of a user with their NEO (None for a generic alert).

        Args:
            id_user (int): ID of the user whose alerts are listed.

        Returns:
            list[tuple[Alert, Neo | None]]: Pairs of (Alert, Neo or None).
        """
        neo_dao = NeoDao()
        return [
            (a, neo_dao.find_by_id_neo(a.neo_id) if a.neo_id else None)
            for a in AlertDao().get_by_userid(id_user)
        ]

    @log
    def update(self, id_user: int, id_alert: int, changes: dict) -> tuple[Alert, Neo | None]:
        """
        Updates an alert of a user.

        Args:
            id_user (int): The id of the user who owns the alert.
            id_alert (int): The id of the alert.
            changes (dict): Fields to modify among 'threshold_km', 'threshold_size',
                and 'is_active'. Other keys are ignored.

        Returns:
            tuple[Alert, Neo | None]: The updated alert and the watched NEO (or None).

        Raises:
            HTTPException: 404 if the user has no such alert.
        """
        alert = self._find_user_alert(id_user, id_alert)

        # Apply only allow-listed fields to avoid unintended attribute overwrites
        for field, value in changes.items():
            if field in UPDATABLE_FIELDS:
                setattr(alert, field, value)

        if not AlertDao().update(alert):
            raise HTTPException(status_code=404, detail="Alert not found")

        neo = NeoDao().find_by_id_neo(alert.neo_id) if alert.neo_id else None
        return alert, neo

    @log
    def remove(self, id_user: int, id_alert: int) -> bool:
        """
        Deletes an alert of a user.

        Args:
            id_user (int): The id of the user who owns the alert.
            id_alert (int): The id of the alert.

        Returns:
            bool: True if the alert was deleted.

        Raises:
            HTTPException: 404 if the user has no such alert.
        """
        alert = self._find_user_alert(id_user, id_alert)
        return AlertDao().delete(alert.id)

    @log
    def check_alerts(self, id_user: int) -> list[tuple[Alert, Neo, CloseApproach]]:
        """
        Finds the upcoming close approaches that trigger an active alert of a user.

        An alert on a NEO looks at that NEO only; a generic alert looks at all NEOs.

        Args:
            id_user (int): ID of the user whose alerts are evaluated.

        Returns:
            list[tuple[Alert, Neo, CloseApproach]]: Triggered (alert, neo, approach) tuples.
        """
        today = date.today().isoformat()
        approach_dao = CloseApproachDao()
        neo_dao = NeoDao()

        triggered = []
        for alert, watched_neo in self.list_alerts(id_user):
            if not alert.is_active or alert.threshold_km is None:
                continue

            # Specific alert checks all approaches for one NEO; generic alert pre-filters upcoming ones
            if alert.neo_id:
                approaches = approach_dao.find_by_id_neo(alert.neo_id)
            else:
                approaches = approach_dao.find_upcoming(
                    today, alert.threshold_km, EARTH, alert.threshold_size
                )

            for approach in approaches:
                neo = watched_neo or neo_dao.find_by_id_neo(approach.id_neo)
                if neo and self._is_triggered(alert, neo, approach, today):
                    triggered.append((alert, neo, approach))
        return triggered

    # ------------------------------------------------------------ helpers
    def _find_user_alert(self, id_user: int, id_alert: int) -> Alert:
        """
        Returns an alert of a user, or raises a 404 if the user has no such alert.

        Args:
            id_user (int): ID of the expected alert owner.
            id_alert (int): ID of the alert to locate.

        Returns:
            Alert: The matching alert belonging to the user.

        Raises:
            HTTPException: 404 if no matching alert is found for this user.
        """
        # Filter by id_user first so another user's alert ID is treated as not found
        alert = next((a for a in AlertDao().get_by_userid(id_user) if a.id == id_alert), None)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @staticmethod
    def _is_triggered(alert: Alert, neo: Neo, approach: CloseApproach, today: str) -> bool:
        """
        Evaluates whether a close approach meets all conditions to trigger an alert.

        Args:
            alert (Alert): Alert rule with distance and optional size thresholds.
            neo (Neo): NEO associated with the close approach.
            approach (CloseApproach): Candidate close approach event.
            today (str): Current date in YYYY-MM-DD format used as lower bound.

        Returns:
            bool: True if all trigger conditions are satisfied, False otherwise.
        """
        if approach.orbiting_body != EARTH:
            return False
        if approach.approach_date is None or approach.miss_distance_km is None:
            return False
        if str(approach.approach_date)[:10] < today:
            return False
        if approach.miss_distance_km > alert.threshold_km:
            return False
        # Treat missing max diameter as 0 when a size threshold is configured
        if alert.threshold_size is not None and (neo.diameter_max_m or 0) < alert.threshold_size:
            return False
        return True
