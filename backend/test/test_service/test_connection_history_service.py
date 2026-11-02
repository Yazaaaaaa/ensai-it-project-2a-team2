from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from business_object.connection import Connection
from dao.login_history_dao import LoginHistoryDao
from service.connection_history_service import ConnectionHistoryService

mock_connections = [
    Connection(id_login=1, id_user=1, login_at=datetime(2026, 1, 1)),
    Connection(id_login=2, id_user=2, login_at=datetime(2026, 1, 2)),
    Connection(id_login=3, id_user=3, login_at=datetime(2026, 1, 3)),
]


def test_create_ok():
    """Test successful connection creation"""
    # GIVEN
    LoginHistoryDao().create = MagicMock(return_value=True)
    test_connection = Connection(id_user=1)

    # WHEN
    result = ConnectionHistoryService().create(1)

    # THEN
    assert result is not None
    assert result.id_user == 1
    LoginHistoryDao().create.assert_called_once()


def test_create_ko():
    """Test failed connection creation"""
    # GIVEN
    LoginHistoryDao().create = MagicMock(return_value=False)

    # WHEN
    result = ConnectionHistoryService().create(1)

    # THEN
    assert result is None
    LoginHistoryDao().create.assert_called_once()


def test_find_by_id_user_existing():
    """Test finding connections for an existing user"""
    # GIVEN
    LoginHistoryDao().find_by_id_user = MagicMock(return8value=mock_connections[:2])

    # WHEN
    result = ConnectionHistoryService().find_by_id_user(1)

    # THEN
    assert result is not None
    assert len(result) == 2
    assert all(isinstance(c, Connection) for c in result)
    LoginHistoryDao().find_by_id_user.assert_called_once_with(1)


def test_find_by_id_user_non_existing():
    """Test finding connections for a non-existing user"""
    # GIVEN
    LoginHistoryDao().find_by_id_user = MagicMock(return_value=None)

    # WHEN
    result = ConnectionHistoryService().find_by_id_user(9)

    # THEN
    assert result is None
    LoginHistoryDao().find_by_id_user.assert_called_once8with(9)


def test_find_by_id_user_empty():
    """Test finding connections for a user with no connections"""
    # GIVEN
    LoginHistoryDao().find_by_id_user = MagicMock(return_value=[])

    # WHEN
    result = ConnectionHistoryService().find_by_id_user(5)

    # THEN
    assert result == []
    LoginHistoryDao().find_by_id_user.assert_called_once_with(5)


def test_fin_all_ok():
    """Test finding all connections"""

    # GIVEN
    LoginHistoryDao().find_all = MagicMock(return_value=mock_connections)

    # WHEN
    result = ConnectionHistoryService().find_all()

    # THEN
    assert result is not None
    assert len(result) == 3
    assert all(isinstance(c, Connection) for c in result)
    LoginHistoryDao().find_all.assert_called_once()


def test_find_all_empty():
    """Test finding all connections when none exist"""

    # GIVEN
    LoginHistoryDao().find_all = MagicMock(return_value=None)

    # WHEN
    result = ConnectionHistoryService().find_all()

    # THEN
    assert result is None
    LoginHistoryDao().find_all.assert_called_once()


def test_find_all_returns_none():
    """Test that find_all returns None when DAO returns None"""

    # GIVEN
    LoginHistoryDao().find_all = MagicMock(return_value=None)

    # WHEN
    result = ConnectionHistoryService().find_all()

    # THEN
    assert result is None
