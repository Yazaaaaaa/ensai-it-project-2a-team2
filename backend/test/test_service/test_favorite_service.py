from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from business_object.favorite import Favorite
from business_object.neo import Neo
from service.favorite_service import FavoriteService

neos = {
    42: Neo(id_neo=42, nasa_id="2004055", name_neo="4055 Magellan", diameter_min_m=2783.0,
            diameter_max_m=6223.0, absolute_magnitude=14.9, is_hazardous=False,
            is_custom=False, created_by_user_id=None),
    7: Neo(id_neo=7, nasa_id="2099942", name_neo="Apophis", diameter_min_m=300,
           diameter_max_m=400, absolute_magnitude=20.0, is_hazardous=True,
           is_custom=False, created_by_user_id=None),
}

favorites = [
    Favorite(id_user=1, id_neo=7, added_at=datetime(2026, 11, 3), id_favorite=2),
    Favorite(id_user=1, id_neo=42, added_at=datetime(2026, 11, 2), id_favorite=1),
]


@pytest.fixture
def daos():
    """Replaces the DAOs used by the service and yields (favorite_dao, neo_dao)."""
    with patch("service.favorite_service.FavoriteDao") as favorite_dao, \
            patch("service.favorite_service.NeoDao") as neo_dao:
        neo_dao.return_value.find_by_id_neo.side_effect = lambda id_neo: neos.get(id_neo)
        yield favorite_dao.return_value, neo_dao.return_value


# ---------------------------------------------------------------- add
def test_add_ok(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.exists.return_value = False
    favorite_dao.create.return_value = True

    # WHEN
    favorite, neo = FavoriteService().add(1, 42)

    # THEN
    assert favorite.id_user == 1
    assert favorite.id_neo == 42
    assert neo.name_neo == "4055 Magellan"
    favorite_dao.create.assert_called_once_with(favorite)


def test_add_neo_not_found(daos):

    # GIVEN
    favorite_dao, _ = daos

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().add(1, 999)

    assert exc.value.status_code == 404
    favorite_dao.exists.assert_not_called()
    favorite_dao.create.assert_not_called()


def test_add_already_favorite(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.exists.return_value = True

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().add(1, 42)

    assert exc.value.status_code == 409
    favorite_dao.create.assert_not_called()


def test_add_creation_failed(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.exists.return_value = False
    favorite_dao.create.return_value = False

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().add(1, 42)

    assert exc.value.status_code == 500


# ---------------------------------------------------------------- list_favorites
def test_list_favorites(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.find_all_by_user.return_value = favorites

    # WHEN
    res = FavoriteService().list_favorites(1)

    # THEN : order of the DAO is kept (most recent first), each favorite comes with its NEO
    assert [f.id_favorite for f, _ in res] == [2, 1]
    assert [n.name_neo for _, n in res] == ["Apophis", "4055 Magellan"]
    favorite_dao.find_all_by_user.assert_called_once_with(1)


def test_list_favorites_empty(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.find_all_by_user.return_value = []

    # WHEN
    res = FavoriteService().list_favorites(99)

    # THEN
    assert res == []


def test_list_favorites_skips_missing_neo(daos):

    # GIVEN : the second favorite refers to a NEO that no longer exists
    favorite_dao, _ = daos
    orphan = Favorite(id_user=1, id_neo=999, id_favorite=3)
    favorite_dao.find_all_by_user.return_value = [favorites[0], orphan]

    # WHEN
    res = FavoriteService().list_favorites(1)

    # THEN
    assert [f.id_favorite for f, _ in res] == [2]


# ---------------------------------------------------------------- remove
def test_remove_ok(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.find_all_by_user.return_value = favorites
    favorite_dao.delete.return_value = True

    # WHEN
    res = FavoriteService().remove(1, 42)

    # THEN : the favorite of NEO 42 is the one deleted
    assert res is True
    favorite_dao.delete.assert_called_once_with(favorites[1])


def test_remove_not_found(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.find_all_by_user.return_value = favorites

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().remove(1, 999)

    assert exc.value.status_code == 404
    favorite_dao.delete.assert_not_called()


def test_remove_user_without_favorites(daos):

    # GIVEN
    favorite_dao, _ = daos
    favorite_dao.find_all_by_user.return_value = []

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().remove(99, 42)

    assert exc.value.status_code == 404
    favorite_dao.delete.assert_not_called()