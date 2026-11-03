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

# Fields of an alert that can be modified after its creation
UPDATABLE_FIELDS = ("threshold_km", "is_active")

# Name of the body used in the close approaches data for the Earth
EARTH = "Earth"


class AlertService:
    """Service that manages the alerts of the users on the NEOs they watch."""

    @log
    def add(
        self,
        id_user: int,
        id_neo: int,
        threshold_km: float,
        is_active: bool = True,
    ) -> tuple[Alert, Neo]:
        """Creates an alert for a user on a NEO.
        Args:
            id_user (int): The id of the user.
            id_neo (int): The id of the NEO to watch.
            threshold_km (float): Distance to the Earth, in km, under which the user
                wants to be notified (compared to the miss distance of an approach).
            is_active (bool, optional): Whether the alert is active. Defaults to True.
        Returns:
            tuple[Alert, Neo]: The created alert and the watched NEO.
        Raises:
            HTTPException: 404 if the NEO does not exist, 409 if the user already watches it.
        """
        neo = NeoDao().find_by_id_neo(id_neo)
        if neo is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        dao = AlertDao()
        if any(a.neo_id == id_neo for a in dao.get_by_userid(id_user)):
            raise HTTPException(status_code=409, detail="This NEO already has an alert")

        alert = Alert(
            user_id=id_user,
            neo_id=id_neo,
            threshold_km=threshold_km,
            is_active=is_active,
        )
        if not dao.create(alert):
            raise HTTPException(status_code=500, detail="The alert could not be created")

        return alert, neo

    @log
    def list_alerts(self, id_user: int) -> list[tuple[Alert, Neo]]:
        """Lists the alerts of a user with the NEO they watch, the most recent first.
        Args:
            id_user (int): The id of the user.
        Returns:
            list[tuple[Alert, Neo]]: The alerts with their NEO (empty list if none).
        """
        neo_dao = NeoDao()
        result = []
        for alert in AlertDao().get_by_userid(id_user):
            neo = neo_dao.find_by_id_neo(alert.neo_id)
            if neo is not None:
                result.append((alert, neo))
        return result

    @log
    def update(self, id_user: int, id_alert: int, changes: dict) -> tuple[Alert, Neo]:
        """Updates an alert of a user.
        Args:
            id_user (int): The id of the user who owns the alert.
            id_alert (int): The id of the alert.
            changes (dict): Fields to modify among 'threshold_km' and 'is_active'.
                Other keys are ignored.
        Returns:
            tuple[Alert, Neo]: The updated alert and the watched NEO.
        Raises:
            HTTPException: 404 if the user has no such alert.
        """
        alert = self._find_user_alert(id_user, id_alert)

        for field, value in changes.items():
            if field in UPDATABLE_FIELDS:
                setattr(alert, field, value)

        if not AlertDao().update(alert):
            raise HTTPException(status_code=404, detail="Alert not found")

        return alert, NeoDao().find_by_id_neo(alert.neo_id)

    @log
    def remove(self, id_user: int, id_alert: int) -> bool:
        """Deletes an alert of a user.
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
        """Finds the upcoming close approaches that trigger an active alert of a user.
        An alert is triggered by an approach of the watched NEO to the Earth that is today
        or later, whose miss_distance_km is at most the 'threshold_km' of the alert.
        Args:
            id_user (int): The id of the user.
        Returns:
            list[tuple[Alert, Neo, CloseApproach]]: One entry per triggering approach.
        """
        today = date.today().isoformat()
        approach_dao = CloseApproachDao()

        triggered = []
        for alert, neo in self.list_alerts(id_user):
            if not alert.is_active:
                continue
            for approach in approach_dao.find_by_id_neo(neo.id_neo):
                if self._is_triggered(alert, approach, today):
                    triggered.append((alert, neo, approach))
        return triggered

    # ------------------------------------------------------------ helpers
    def _find_user_alert(self, id_user: int, id_alert: int) -> Alert:
        """Returns an alert of a user, or raises a 404 if the user has no such alert."""
        alert = next((a for a in AlertDao().get_by_userid(id_user) if a.id == id_alert), None)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @staticmethod
    def _is_triggered(alert: Alert, approach: CloseApproach, today: str) -> bool:
        """Tells whether a close approach triggers an alert (see check_alerts)."""
        if alert.threshold_km is None:
            return False

        if approach.orbiting_body != EARTH:
            return False

        if approach.approach_date is None or approach.miss_distance_km is None:
            return False

        # ISO dates (YYYY-MM-DD...) can be compared as strings
        if str(approach.approach_date)[:10] < today:
            return False

        return approach.miss_distance_km <= alert.threshold_km