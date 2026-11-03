import pytest

from business_object.favorite import Favorite
from dao.favorite_dao import FavoriteDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    ResetDatabase().run(test_dao=True)


# ---------------------------------------------------------------- create
def test_create_ok():
    """Successfully create a favorite"""

    # GIVEN : Bob (2) does not have Eros (1) in his favorites yet
    favorite = Favorite(id_user=2, id_neo=1)

    # WHEN
    creation_ok = FavoriteDao().create(favorite)

    # THEN
    assert creation_ok
    assert favorite.id_favorite
    assert favorite.added_at is not None
    assert FavoriteDao().exists(2, 1)


# ---------------------------------------------------------------- find_by_id
def test_find_by_id_found():
    """Find a favorite by an existing id"""

    # WHEN
    found = FavoriteDao().find_by_id(1)

    # THEN
    assert isinstance(found, Favorite)
    assert found.id_user == 1
    assert found.id_neo == 1
    assert found.added_at is not None


def test_find_by_id_not_found():
    """Find a favorite by a non-existing id"""

    # WHEN
    found = FavoriteDao().find_by_id(999999999)

    # THEN
    assert found is None


# ---------------------------------------------------------------- find_all_by_user
def test_find_all_by_user_ok():
    """Find all the favorites of a user"""

    # WHEN
    favorites = FavoriteDao().find_all_by_user(1)

    # THEN : Alice has Eros (1) and Apophis (2)
    assert all(isinstance(f, Favorite) for f in favorites)
    assert all(f.id_user == 1 for f in favorites)
    assert {f.id_neo for f in favorites} == {1, 2}


def test_find_all_by_user_no_favorite():
    """A user with no favorite gets an empty list"""

    # WHEN
    favorites = FavoriteDao().find_all_by_user(5)

    # THEN
    assert favorites == []


# ---------------------------------------------------------------- exists
def test_exists_true():
    """The favorite (Alice, Eros) exists"""

    # WHEN / THEN
    assert FavoriteDao().exists(1, 1) is True


def test_exists_false():
    """The favorite (Alice, Bennu) does not exist"""

    # WHEN / THEN
    assert FavoriteDao().exists(1, 3) is False


# ---------------------------------------------------------------- delete
def test_delete_ok():
    """Successfully delete a favorite that has a distance history"""

    # GIVEN : favorite 2 (Alice, Apophis) has a row in distance_history
    favorite = FavoriteDao().find_by_id(2)

    # WHEN
    delete_ok = FavoriteDao().delete(favorite)

    # THEN : no foreign key error, the favorite is gone
    assert delete_ok
    assert FavoriteDao().find_by_id(2) is None
    assert FavoriteDao().exists(1, 2) is False


def test_delete_not_found():
    """Deleting a non-existing favorite returns False"""

    # GIVEN
    favorite = Favorite(id_user=1, id_neo=1, id_favorite=999999999)

    # WHEN
    delete_ok = FavoriteDao().delete(favorite)

    # THEN
    assert delete_ok is False