import os
from datetime import datetime
from unittest.mock import patch

import psycopg2
import pytest

from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


def test_create_ok():
    """Successfully create a new login history"""

    # GIVEN
    login = Connection(id_user=1, id_login=1, timestamp=datetime.now())

    # WHEN
    creation_ok = LoginHistoryDao().create(login)

    # THEN
    assert creation_ok
    assert login.id_login
    assert login.login_at


def test_create_ko():
    """Fail to create a new login history (invalid id_user or id_login)"""

    # GIVEN
    login = Connection(id_user="1", id_login="1", timestamp=datetime.now())

    # WHEN / THEN
    with pytest.raises(psycopg2.Error):
        LoginHistoryDao().create(login)