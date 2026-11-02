import os
from datetime import datetime
from unittest.mock import patch

import psycopg2
import pytest

from business_object.alert import Alert
from business_object.neo import Neo
from business_object.user import User
from dao.alert_dao import AlertDao
from dao.neo_dao import NeoDao
from dao.user_dao import UserDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


@pytest.fixture
def user():
    user = User(id_user=None, email="test@ensai.fr", password_hash="hash",
                role_user="user", token="tok", created_at=datetime.now())
    assert UserDao().create(user) is True
    assert user.id_user is not None
    yield user
    UserDao().delete(user)


@pytest.fixture
def neo():
    neo = Neo(nasa_id="TEST_123", name_neo="TEST", diameter_min_m=10, diameter_max_m=20)
    NeoDao().create(neo)
    assert neo.id_neo is not None
    yield neo
    NeoDao().delete(neo.id_neo)


@pytest.fixture
def alert(user, neo):
    """Alerte existante en base. Supprimée avant le neo et le user (ordre inverse de création)."""
    alert = Alert(user_id=user.id_user, neo_id=neo.id_neo,
                  min_size_m=10.0, max_distance_km=1000.0, is_active=True)
    assert AlertDao().create(alert) is True
    assert alert.id is not None
    yield alert
    AlertDao().delete(alert.id)  # renvoie False si le test l'a déjà supprimée, sans conséquence


# ---------------------------------------------------------------- create

def test_create_ok(user, neo):
    """Successfully create an Alert"""
    # GIVEN
    alert = Alert(user_id=user.id_user, neo_id=neo.id_neo,
                  min_size_m=50.0, max_distance_km=50000.0, is_active=True)
    try:
        # WHEN
        created = AlertDao().create(alert)

        # THEN
        assert created is True
        assert alert.id is not None
    finally:
        if alert.id is not None:
            AlertDao().delete(alert.id)


def test_create_ko(user):
    """Fail to create an Alert (neo_id inexistant -> violation de clé étrangère)"""
    # GIVEN
    alert = Alert(user_id=user.id_user, neo_id=999999,
                  min_size_m=50.0, max_distance_km=50000.0, is_active=True)

    # WHEN
    try:
        created = AlertDao().create(alert)
    except psycopg2.Error:
        created = False  # le DAO laisse remonter l'erreur SQL

    # THEN
    assert created is False
    assert alert.id is None


# ---------------------------------------------------------- get_by_userid

def test_get_by_userid_existing(alert, user):
    """Retrieve alerts for an existing user"""
    # WHEN
    alerts = AlertDao().get_by_userid(user.id_user)

    # THEN
    assert isinstance(alerts, list)
    assert len(alerts) >= 1
    assert all(isinstance(a, Alert) for a in alerts)
    assert all(a.user_id == user.id_user for a in alerts)
    assert alert.id in [a.id for a in alerts]


def test_get_by_userid_empty(user):
    """Retrieve alerts for a user with no alerts"""
    # WHEN (le user existe mais n'a aucune alerte)
    alerts = AlertDao().get_by_userid(user.id_user)

    # THEN
    assert isinstance(alerts, list)
    assert alerts == []


def test_get_by_userid_unknown_user():
    """Retrieve alerts for a user id that does not exist"""
    # WHEN
    alerts = AlertDao().get_by_userid(999999)

    # THEN
    assert alerts == []


# ----------------------------------------------------------------- update

def test_update_ok(alert, user):
    """Successfully update an existing Alert"""
    # GIVEN
    alert.max_distance_km = 25000.0
    alert.is_active = False

    # WHEN
    update_ok = AlertDao().update(alert)

    # THEN
    assert update_ok is True
    stored = next(a for a in AlertDao().get_by_userid(user.id_user) if a.id == alert.id)
    assert stored.max_distance_km == 25000.0
    assert stored.is_active is False


def test_update_ko(user, neo):
    """Fail to update an Alert (unknown id)"""
    # GIVEN
    alert = Alert(id=888888, user_id=user.id_user, neo_id=neo.id_neo,
                  min_size_m=10.0, max_distance_km=10000.0, is_active=True)

    # WHEN
    update_ok = AlertDao().update(alert)

    # THEN
    assert not update_ok


# ----------------------------------------------------------------- delete

def test_delete_ok(user, neo):
    """Successfully delete an Alert"""
    # GIVEN (alerte dédiée à ce test)
    alert_to_delete = Alert(user_id=user.id_user, neo_id=neo.id_neo,
                            min_size_m=15.0, max_distance_km=15000.0, is_active=True)
    assert AlertDao().create(alert_to_delete) is True

    # WHEN
    delete_ok = AlertDao().delete(alert_to_delete.id)

    # THEN
    assert delete_ok
    remaining = [a.id for a in AlertDao().get_by_userid(user.id_user)]
    assert alert_to_delete.id not in remaining


def test_delete_ko():
    """Fail to delete an Alert (unknown id)"""
    # WHEN
    delete_ok = AlertDao().delete(888888)

    # THEN
    assert not delete_ok


if __name__ == "__main__":
    pytest.main([__file__])