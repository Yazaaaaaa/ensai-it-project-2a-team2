import psycopg2
import pytest

from business_object.alert import Alert
from dao.alert_dao import AlertDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    ResetDatabase().run(test_dao=True)


# ---------------------------------------------------------------- create
def test_create_ok():
    """Successfully create an Alert"""

    # GIVEN : Bob (2) has no alert on Bennu (3) in the test data
    alert = Alert(user_id=2, neo_id=3, threshold_km=50000.0, is_active=True)

    # WHEN
    created = AlertDao().create(alert)

    # THEN
    assert created is True
    assert alert.id is not None
    assert alert.id in [a.id for a in AlertDao().get_by_userid(2)]


def test_create_ko():
    """Fail to create an Alert (unknown neo_id -> foreign key violation)"""

    # GIVEN
    alert = Alert(user_id=1, neo_id=999999, threshold_km=50000.0, is_active=True)

    # WHEN
    try:
        created = AlertDao().create(alert)
    except psycopg2.Error:
        created = False  # the DAO lets the SQL error go up

    # THEN
    assert created is False
    assert alert.id is None


def test_create_global_alert_with_size():
    """Successfully create an Alert on any NEO, with a minimal size"""

    # GIVEN
    alert = Alert(user_id=2, neo_id=None, threshold_km=5000000.0, threshold_size=100.0,
                  is_active=True)

    # WHEN
    created = AlertDao().create(alert)

    # THEN
    assert created is True
    stored = next(a for a in AlertDao().get_by_userid(2) if a.id == alert.id)
    assert stored.neo_id is None
    assert stored.threshold_size == pytest.approx(100.0)


# ---------------------------------------------------------- get_by_userid
def test_get_by_userid_existing():
    """Retrieve the alerts of a user"""

    # WHEN : Alice (1) has alert 1 (on Eros) and alert 2 (on every NEO)
    alerts = AlertDao().get_by_userid(1)

    # THEN
    assert isinstance(alerts, list)
    assert all(isinstance(a, Alert) for a in alerts)
    assert all(a.user_id == 1 for a in alerts)
    assert {a.id for a in alerts} == {1, 2}


def test_get_by_userid_global_alert():
    """An alert without neo_id is returned with neo_id None"""

    # WHEN
    alerts = AlertDao().get_by_userid(1)

    # THEN
    global_alert = next(a for a in alerts if a.id == 2)
    assert global_alert.neo_id is None
    assert global_alert.threshold_km == pytest.approx(500000.0)
    assert global_alert.is_active is True


def test_get_by_userid_empty():
    """A user with no alert gets an empty list"""

    # WHEN : empty@test.com (5) has no alert
    alerts = AlertDao().get_by_userid(5)

    # THEN
    assert alerts == []


def test_get_by_userid_unknown_user():
    """An unknown user id gets an empty list"""

    # WHEN
    alerts = AlertDao().get_by_userid(999999)

    # THEN
    assert alerts == []



# ---------------------------------------------------------------- update
def test_update_ok():
    """Successfully update an existing Alert"""

    # GIVEN : alert 3 (Bob, Apophis, inactive)
    alert = next(a for a in AlertDao().get_by_userid(2) if a.id == 3)
    alert.threshold_km = 25000.0
    alert.threshold_size = 150.0
    alert.is_active = True

    # WHEN
    update_ok = AlertDao().update(alert)

    # THEN
    assert update_ok is True
    stored = next(a for a in AlertDao().get_by_userid(2) if a.id == 3)
    assert stored.threshold_km == pytest.approx(25000.0)
    assert stored.threshold_size == pytest.approx(150.0)
    assert stored.is_active is True


def test_update_ko():
    """Fail to update an Alert (unknown id)"""

    # GIVEN
    alert = Alert(id=888888, user_id=1, neo_id=1, threshold_km=10000.0, is_active=True)

    # WHEN
    update_ok = AlertDao().update(alert)

    # THEN
    assert not update_ok


# ---------------------------------------------------------------- delete
def test_delete_ok():
    """Successfully delete an Alert"""

    # WHEN : alert 2 (Alice, all NEOs)
    delete_ok = AlertDao().delete(2)

    # THEN
    assert delete_ok
    assert 2 not in [a.id for a in AlertDao().get_by_userid(1)]


def test_delete_ko():
    """Fail to delete an Alert (unknown id)"""

    # WHEN
    delete_ok = AlertDao().delete(888888)

    # THEN
    assert not delete_ok