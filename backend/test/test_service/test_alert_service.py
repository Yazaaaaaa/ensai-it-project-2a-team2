from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from business_object.alert import Alert
from business_object.close_approach import CloseApproach
from business_object.neo import Neo
from dao.alert_dao import AlertDao
from dao.close_approach_dao import CloseApproachDao
from dao.neo_dao import NeoDao
from service.alert_service import AlertService

TODAY = date.today().isoformat()
FUTURE = (date.today() + timedelta(days=30)).isoformat()
PAST = (date.today() - timedelta(days=30)).isoformat()

eros = Neo(id_neo=1, nasa_id="2000433", name_neo="Eros", diameter_min_m=100, diameter_max_m=200,
           absolute_magnitude=10.0, is_hazardous=False, is_custom=False, created_by_user_id=None)
small = Neo(id_neo=2, nasa_id="2099942", name_neo="Small", diameter_min_m=10, diameter_max_m=20,
            absolute_magnitude=25.0, is_hazardous=False, is_custom=False, created_by_user_id=None)
unknown_size = Neo(id_neo=3, nasa_id="CUSTOM-1", name_neo="Custom", diameter_min_m=None,
                   diameter_max_m=None, absolute_magnitude=None, is_hazardous=False,
                   is_custom=True, created_by_user_id=7)


def make_alert(**kwargs) -> Alert:
    """Alert on any NEO (>= 100 m, within 5 million km) unless overridden."""
    values = {"id": 1, "user_id": 10, "neo_id": None, "threshold_km": 5000000.0,
              "threshold_size": 100.0, "is_active": True}
    return Alert(**{**values, **kwargs})


def make_approach(**kwargs) -> CloseApproach:
    """Future approach of Eros to the Earth at 1.5 million km unless overridden."""
    values = {"id_approach": 101, "id_neo": 1, "approach_date": FUTURE,
              "orbiting_body": "Earth", "miss_distance_km": 1500000.0,
              "relative_velocity_kmh": 50000.0}
    return CloseApproach(**{**values, **kwargs})


def patch_dao(monkeypatch, dao, method, value):
    """Replaces a DAO method by a mock, restored at the end of the test."""
    mock = MagicMock(return_value=value)
    monkeypatch.setattr(dao(), method, mock)
    return mock


# ---------------------------------------------------------------- add
def test_add_on_neo_ok(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", eros)
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [])
    create = patch_dao(monkeypatch, AlertDao, "create", True)

    # WHEN
    alert, neo = AlertService().add(10, 1, 5000000.0, 100.0)

    # THEN
    assert neo is eros
    assert alert.neo_id == 1
    assert alert.threshold_size == 100.0
    create.assert_called_once_with(alert)


def test_add_on_any_neo_ok(monkeypatch):

    # GIVEN : an existing alert on a NEO must not block a generic alert
    find_neo = patch_dao(monkeypatch, NeoDao, "find_by_id_neo", None)
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(id=5, neo_id=1)])
    create = patch_dao(monkeypatch, AlertDao, "create", True)

    # WHEN
    alert, neo = AlertService().add(10, None, 5000000.0, 100.0)

    # THEN
    assert neo is None
    assert alert.neo_id is None
    assert alert.threshold_size == 100.0
    find_neo.assert_not_called()
    create.assert_called_once_with(alert)


def test_add_neo_not_found(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", None)
    create = patch_dao(monkeypatch, AlertDao, "create", True)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        AlertService().add(10, 999, 5000000.0)

    assert exc.value.status_code == 404
    create.assert_not_called()


def test_add_already_watched(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", eros)
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(neo_id=1)])
    create = patch_dao(monkeypatch, AlertDao, "create", True)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        AlertService().add(10, 1, 5000000.0)

    assert exc.value.status_code == 409
    create.assert_not_called()


def test_add_creation_fails(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [])
    patch_dao(monkeypatch, AlertDao, "create", False)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        AlertService().add(10, None, 5000000.0)

    assert exc.value.status_code == 500


# ---------------------------------------------------------------- list_alerts
def test_list_alerts(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(id=1, neo_id=1), make_alert(id=2)])
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", eros)

    # WHEN
    res = AlertService().list_alerts(10)

    # THEN : the generic alert has no NEO
    assert [(a.id, n) for a, n in res] == [(1, eros), (2, None)]


def test_list_alerts_empty(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [])

    # WHEN
    res = AlertService().list_alerts(10)

    # THEN
    assert res == []


# ---------------------------------------------------------------- update
def test_update_ok(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(neo_id=1)])
    update = patch_dao(monkeypatch, AlertDao, "update", True)
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", eros)

    # WHEN : neo_id is not an updatable field, it must be ignored
    alert, neo = AlertService().update(10, 1, {"threshold_size": 50.0, "is_active": False,
                                                "neo_id": 99})

    # THEN
    assert alert.threshold_size == 50.0
    assert alert.is_active is False
    assert alert.neo_id == 1
    assert neo is eros
    update.assert_called_once_with(alert)


def test_update_generic_alert(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert()])
    patch_dao(monkeypatch, AlertDao, "update", True)
    find_neo = patch_dao(monkeypatch, NeoDao, "find_by_id_neo", None)

    # WHEN
    alert, neo = AlertService().update(10, 1, {"threshold_km": 1000000.0})

    # THEN
    assert alert.threshold_km == 1000000.0
    assert neo is None
    find_neo.assert_not_called()


def test_update_not_found(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [])
    update = patch_dao(monkeypatch, AlertDao, "update", True)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        AlertService().update(10, 999, {"is_active": False})

    assert exc.value.status_code == 404
    update.assert_not_called()


# ---------------------------------------------------------------- remove
def test_remove_ok(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(id=3)])
    delete = patch_dao(monkeypatch, AlertDao, "delete", True)

    # WHEN
    res = AlertService().remove(10, 3)

    # THEN
    assert res is True
    delete.assert_called_once_with(3)


def test_remove_not_found(monkeypatch):

    # GIVEN : the alert exists but belongs to another user, so the user has none
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [])
    delete = patch_dao(monkeypatch, AlertDao, "delete", True)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        AlertService().remove(10, 3)

    assert exc.value.status_code == 404
    delete.assert_not_called()


# ---------------------------------------------------------------- check_alerts
def test_check_alerts_any_neo(monkeypatch):

    # GIVEN
    approach = make_approach()
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert()])
    upcoming = patch_dao(monkeypatch, CloseApproachDao, "find_upcoming", [approach])
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", eros)

    # WHEN
    res = AlertService().check_alerts(10)

    # THEN : the search covers all NEOs, with the thresholds of the alert
    assert [(a.id, n, c) for a, n, c in res] == [(1, eros, approach)]
    upcoming.assert_called_once_with(TODAY, 5000000.0, "Earth", 100.0)


def test_check_alerts_on_one_neo(monkeypatch):

    # GIVEN : only the future approach under the threshold must remain
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(neo_id=1)])
    patch_dao(monkeypatch, NeoDao, "find_by_id_neo", eros)
    patch_dao(monkeypatch, CloseApproachDao, "find_by_id_neo", [
        make_approach(id_approach=101),
        make_approach(id_approach=102, approach_date=PAST),
        make_approach(id_approach=103, miss_distance_km=9000000.0),
    ])
    upcoming = patch_dao(monkeypatch, CloseApproachDao, "find_upcoming", [])

    # WHEN
    res = AlertService().check_alerts(10)

    # THEN
    assert [c.id_approach for _, _, c in res] == [101]
    upcoming.assert_not_called()


def test_check_alerts_inactive(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [make_alert(is_active=False)])
    upcoming = patch_dao(monkeypatch, CloseApproachDao, "find_upcoming", [make_approach()])

    # WHEN
    res = AlertService().check_alerts(10)

    # THEN
    assert res == []
    upcoming.assert_not_called()


def test_check_alerts_no_alert(monkeypatch):

    # GIVEN
    patch_dao(monkeypatch, AlertDao, "get_by_userid", [])

    # WHEN
    res = AlertService().check_alerts(10)

    # THEN
    assert res == []


# ---------------------------------------------------------------- _is_triggered
def test_is_triggered_ok():

    # WHEN / THEN
    assert AlertService._is_triggered(make_alert(), eros, make_approach(), TODAY) is True


@pytest.mark.parametrize("changes", [
    {"orbiting_body": "Mars"},
    {"approach_date": PAST},
    {"approach_date": None},
    {"miss_distance_km": 9000000.0},
    {"miss_distance_km": None},
])
def test_is_triggered_ko_approach(changes):

    # WHEN / THEN
    assert AlertService._is_triggered(make_alert(), eros, make_approach(**changes), TODAY) is False


def test_is_triggered_neo_too_small():

    # WHEN / THEN : 20 m < 100 m
    assert AlertService._is_triggered(make_alert(), small, make_approach(id_neo=2), TODAY) is False


def test_is_triggered_unknown_size_with_size_threshold():

    # WHEN / THEN
    approach = make_approach(id_neo=3)
    assert AlertService._is_triggered(make_alert(), unknown_size, approach, TODAY) is False


def test_is_triggered_without_size_threshold():

    # GIVEN : no size criteria, so any size is accepted
    alert = make_alert(threshold_size=None)

    # WHEN / THEN
    assert AlertService._is_triggered(alert, small, make_approach(id_neo=2), TODAY) is True
    assert AlertService._is_triggered(alert, unknown_size, make_approach(id_neo=3), TODAY) is True