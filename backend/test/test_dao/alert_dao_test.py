import os
from unittest.mock import patch

import psycopg2
import pytest

from business_object.alert import Alert
from dao.alert_dao import AlertDao
from business_object.user import User
from dao.user_dao import UserDao
from business_object.neo import Neo
from dao.neo_dao import NeoDao
from utils.reset_database import ResetDatabase
from datetime import datetime



@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


@pytest.fixture
def user():
    user = User(id_user=1, email="test@ensai.fr", password_hash="hashed_pwd",
                role_user="user", token="token123", created_at=datetime.now())
    UserDao().create(user)
    yield user
    UserDao().delete(user)

@pytest.fixture
def neo():
    neo = Neo(id_nasa="Test_123", name_neo="TEST", id_neo=1)
    NeoDao().create(neo)
    yield neo
    NeoDao().delete(neo)

def test_create_ok(user, neo):
    alert = Alert(user_id=user.id_user, neo_id=neo.id_neo,
                  min_size_m=50.0, max_distance_km=50000.0, is_active=True)

    assert AlertDao().create(alert) is True
    assert alert.id is not None


def test_create_ko():
    """Fail to create an Alert (invalid foreign key or data type)"""

    # GIVEN (ID utilisateur inexistant ou types invalides provoquant une erreur SQL)
    alert = Alert(user_id=999999, neo_id=None, threshold_km="invalid_value", is_active=True)

    # WHEN / THEN
    with pytest.raises(psycopg2.Error):
        AlertDao().create(alert)


def test_get_by_userid_existing():
    """Retrieve alerts for an existing user id"""

    # GIVEN
    user_id = 1

    # WHEN
    alerts = AlertDao().get_by_userid(user_id)

    # THEN
    assert isinstance(alerts, list)
    for a in alerts:
        assert isinstance(a, Alert)
        assert a.user_id == user_id


def test_get_by_userid_empty():
    """Retrieve alerts for a user with no alerts"""

    # GIVEN
    user_id = 999999

    # WHEN
    alerts = AlertDao().get_by_userid(user_id)

    # THEN
    assert isinstance(alerts, list)
    assert len(alerts) == 0


def test_update_ok():
    """Successfully update an existing Alert"""

    # GIVEN (On suppose que l'alerte ID 1 existe suite au ResetDatabase ou création préalable)
    alert = Alert(id=1, user_id=1, neo_id="2023_AB", threshold_km=25000.0, is_active=False)

    # WHEN
    update_ok = AlertDao().update(alert)

    # THEN
    assert update_ok


def test_update_ko():
    """Fail to update an Alert (unknown id)"""

    # GIVEN
    alert = Alert(id=8888, user_id=1, neo_id="2023_AB", threshold_km=10000.0, is_active=True)

    # WHEN
    update_ok = AlertDao().update(alert)

    # THEN
    assert not update_ok


def test_delete_ok():
    """Successfully delete an Alert"""

    # GIVEN (On crée une alerte dédiée pour s'assurer qu'elle existe et peut être supprimée)
    alert_to_delete = Alert(user_id=1, neo_id="2023_AC", threshold_km=15000.0, is_active=True)
    AlertDao().create(alert_to_delete)
    alert_id = alert_to_delete.id

    # WHEN
    delete_ok = AlertDao().delete(alert_id)

    # THEN
    assert delete_ok


def test_delete_ko():
    """Fail to delete an Alert (unknown id)"""

    # GIVEN
    alert_id = 8888

    # WHEN
    delete_ok = AlertDao().delete(alert_id)

    # THEN
    assert not delete_ok


if __name__ == "__main__":
    pytest.main([__file__])