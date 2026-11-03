from fastapi import APIRouter

from schema.alert_schema import (
    AlertIn,
    AlertOut,
    AlertUpdate,
    TriggeredAlertOut,
    _alert_to_out,
    _triggered_to_out,
)
from service.alert_service import AlertService

router = APIRouter()


@router.post("", response_model=AlertOut, status_code=201)
def create_alert(body: AlertIn):
    """Creates an alert on a NEO for a user."""
    alert, neo = AlertService().add(body.id_user, body.id_neo, body.threshold_km, body.is_active)
    return _alert_to_out(alert, neo)


@router.get("/{id_user}", response_model=list[AlertOut])
def list_alerts(id_user: int):
    """Lists all the NEOs watched by a user (most recent alert first)."""
    alerts = AlertService().list_alerts(id_user)
    return [_alert_to_out(a, n) for a, n in alerts]


@router.get("/{id_user}/triggered", response_model=list[TriggeredAlertOut])
def get_triggered_alerts(id_user: int):
    """Lists the upcoming close approaches that trigger an active alert of a user."""
    triggered = AlertService().check_alerts(id_user)
    return [_triggered_to_out(a, n, c) for a, n, c in triggered]


@router.patch("/{id_user}/{id_alert}", response_model=AlertOut)
def update_alert(id_user: int, id_alert: int, body: AlertUpdate):
    """Modifies an alert (only the fields sent in the body are changed)."""
    alert, neo = AlertService().update(id_user, id_alert, body.model_dump(exclude_unset=True))
    return _alert_to_out(alert, neo)


@router.delete("/{id_user}/{id_alert}", status_code=204)
def delete_alert(id_user: int, id_alert: int):
    """Deletes an alert of a user."""
    AlertService().remove(id_user, id_alert)