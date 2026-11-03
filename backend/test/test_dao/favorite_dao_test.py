from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from business_object.favorite import Favorite
from dao.favorite_dao import FavoriteDao

ADDED_AT = datetime(2026, 11, 3, 9, 5, 17)


@pytest.fixture
def cursor():
    """Replaces the database connection by a mock and yields the mocked cursor.

    No real database is touched: the tests check the SQL parameters sent by the DAO
    and the way it converts the returned rows.
    """
    with patch("dao.favorite_dao.DBConnection") as db:
        cur = MagicMock()
        connection = db.return_value.connection.__enter__.return_value
        connection.cursor.return_value.__enter__.return_value = cur
        yield cur


# ---------------------------------------------------------------- create
def test_create_ok(cursor):

    # GIVEN
    cursor.fetchone.return_value = {"id_favorite": 5, "added_at": ADDED_AT}
    favorite = Favorite(id_user=1, id_neo=42)

    # WHEN
    res = FavoriteDao().create(favorite)

    # THEN
    assert res is True
    assert favorite.id_favorite == 5
    assert favorite.added_at == ADDED_AT
    assert cursor.execute.call_args[0][1] == {"id_user": 1, "id_neo": 42}


def test_create_no_row_returned(cursor):

    # GIVEN
    cursor.fetchone.return_value = None
    favorite = Favorite(id_user=1, id_neo=42)

    # WHEN
    res = FavoriteDao().create(favorite)

    # THEN
    assert res is False
    assert favorite.id_favorite is None


def test_create_database_error(cursor):

    # GIVEN
    cursor.execute.side_effect = Exception("DB error")

    # WHEN / THEN
    with pytest.raises(Exception, match="DB error"):
        FavoriteDao().create(Favorite(id_user=1, id_neo=42))


# ---------------------------------------------------------------- find_by_id
def test_find_by_id_found(cursor):

    # GIVEN
    cursor.fetchone.return_value = {
        "id_favorite": 3, "id_user": 1, "id_neo": 42, "added_at": ADDED_AT,
    }

    # WHEN
    res = FavoriteDao().find_by_id(3)

    # THEN
    assert isinstance(res, Favorite)
    assert res.id_favorite == 3
    assert res.id_user == 1
    assert res.id_neo == 42
    assert res.added_at == ADDED_AT
    assert cursor.execute.call_args[0][1] == {"id_favorite": 3}


def test_find_by_id_not_found(cursor):

    # GIVEN
    cursor.fetchone.return_value = None

    # WHEN
    res = FavoriteDao().find_by_id(999)

    # THEN
    assert res is None


# ---------------------------------------------------------------- find_all_by_user
def test_find_all_by_user(cursor):

    # GIVEN : rows already ordered by the query (most recent first)
    cursor.fetchall.return_value = [
        {"id_favorite": 2, "id_user": 1, "id_neo": 7, "added_at": ADDED_AT},
        {"id_favorite": 1, "id_user": 1, "id_neo": 42, "added_at": datetime(2026, 11, 2)},
    ]

    # WHEN
    res = FavoriteDao().find_all_by_user(1)

    # THEN
    assert [f.id_favorite for f in res] == [2, 1]
    assert [f.id_neo for f in res] == [7, 42]
    assert all(f.id_user == 1 for f in res)
    assert cursor.execute.call_args[0][1] == {"id_user": 1}


def test_find_all_by_user_empty(cursor):

    # GIVEN
    cursor.fetchall.return_value = []

    # WHEN
    res = FavoriteDao().find_all_by_user(99)

    # THEN
    assert res == []


# ---------------------------------------------------------------- exists
def test_exists_true(cursor):

    # GIVEN
    cursor.fetchone.return_value = {"?column?": 1}

    # WHEN
    res = FavoriteDao().exists(1, 42)

    # THEN
    assert res is True
    assert cursor.execute.call_args[0][1] == {"id_user": 1, "id_neo": 42}


def test_exists_false(cursor):

    # GIVEN
    cursor.fetchone.return_value = None

    # WHEN
    res = FavoriteDao().exists(1, 999)

    # THEN
    assert res is False


# ---------------------------------------------------------------- delete
def test_delete_ok(cursor):

    # GIVEN
    cursor.rowcount = 1
    favorite = Favorite(id_user=1, id_neo=42, id_favorite=3)

    # WHEN
    res = FavoriteDao().delete(favorite)

    # THEN : the distance history is deleted first, then the favorite
    assert res is True
    calls = cursor.execute.call_args_list
    assert len(calls) == 2
    assert "distance_history" in calls[0][0][0]
    assert calls[0][0][1] == {"id_favorite": 3}
    assert "favorite" in calls[1][0][0]
    assert "distance_history" not in calls[1][0][0]
    assert calls[1][0][1] == {"id_favorite": 3}


def test_delete_not_found(cursor):

    # GIVEN
    cursor.rowcount = 0
    favorite = Favorite(id_user=1, id_neo=42, id_favorite=999)

    # WHEN
    res = FavoriteDao().delete(favorite)

    # THEN
    assert res is False


def test_delete_database_error(cursor):

    # GIVEN
    cursor.execute.side_effect = Exception("DB error")

    # WHEN / THEN
    with pytest.raises(Exception, match="DB error"):
        FavoriteDao().delete(Favorite(id_user=1, id_neo=42, id_favorite=3))