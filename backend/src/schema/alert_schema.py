from datetime import datetime

from pydantic import BaseModel, Field

from business_object.alert import Alert
from business_object.close_approach import CloseApproach
from business_object.neo import Neo
from schema.neo_schema import CloseApproachOut, NeoOut, _approach_to_out, _to_out


class AlertIn(BaseModel):
    """Body to create an alert on a NEO."""
    id_user: int
    id_neo: int | None = None
    threshold_km: float = Field(
        ..., gt=0, description="Distance to the Earth, in km, under which the user is notified"
    )
    is_active: bool = True
    threshold_size: float | None = None


class AlertUpdate(BaseModel):
    """Body to modify an alert: only the fields that are sent are changed."""
    threshold_km: float | None = Field(None, gt=0)
    is_active: bool | None = None
    threshold_size: float | None = None


class AlertOut(BaseModel):
    """Alert returned by the API, with the NEO it watches."""
    id_alert: int | None
    id_user: int
    id_neo: int | None = None
    threshold_km: float | None
    threshold_size: float | None = None
    is_active: bool
    created_at: datetime | None
    neo: NeoOut | None = None


class TriggeredAlertOut(BaseModel):
    """An alert and the close approach that triggers it."""
    alert: AlertOut
    neo: NeoOut
    close_approach: CloseApproachOut


def _alert_to_out(alert: Alert, neo: Neo) -> AlertOut:
    """Converts an Alert and its Neo into their API representation."""
    return AlertOut(
        id_alert=alert.id,
        id_user=alert.user_id,
        id_neo=alert.neo_id,
        threshold_km=alert.threshold_km,
        threshold_size=alert.threshold_size,
        is_active=alert.is_active,
        created_at=alert.created_at,
        neo=_to_out(neo) if neo else None,
    )


def _triggered_to_out(alert: Alert, neo: Neo, approach: CloseApproach) -> TriggeredAlertOut:
    """Converts a triggered alert and its close approach into their API representation."""
    return TriggeredAlertOut(
        alert=_alert_to_out(alert, neo),
        neo=_to_out(neo),
        close_approach=_approach_to_out(approach),
    )