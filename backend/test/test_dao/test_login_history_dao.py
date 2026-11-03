from datetime import datetime

import psycopg2
import pytest

from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    ResetDatabase().run(test_dao=True)


def test_create_ok():
    """Successfully create a new login history"""

    # GIVEN
    login = Connection(id_user=4, id_login=None, login_at=datetime.now())

    # WHEN
    creation_ok = LoginHistoryDao().create(login)

    # THEN
    assert creation_ok
    assert login.id_login
    assert login.login_at


def test_create_ko():
    """Fail to create a new login history (invalid id_user or id_login)"""

    # GIVEN
    login = Connection(id_user="a", id_login="a", login_at=datetime.now())

    # WHEN / THEN
    with pytest.raises(psycopg2.Error):
        LoginHistoryDao().create(login)


def test_find_by_id_user_existing():
    """Find connections by an existing user id"""

    # WHEN
    connections = LoginHistoryDao().find_by_id_user(1)

    # THEN
    assert len(connections) == 2
    assert all(c.id_user == 1 for c in connections)


def test_find_by_id_user_non_existing():
    """Find connections by a non-existing user id"""

    # WHEN
    connections = LoginHistoryDao().find_by_id_user(9999999999999)

    # THEN
    assert connections is None


def test_find_all():
    """Verify the method returns a list of Connections objects"""

    # WHEN
    connections = LoginHistoryDao().find_all()

    # THEN
    assert isinstance(connections, list)
    assert len(connections) >= 4
    assert all(isinstance(c, Connection) for c in connections)