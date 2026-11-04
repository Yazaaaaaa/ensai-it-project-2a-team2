from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from business_object.close_approach import CloseApproach
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


def make_approach(**kwargs) -> CloseApproach:
    """Approach of Apophis (7) to the Earth at 1 million km unless overridden."""
    values = {"id_approach": 1, "id_neo": 7, "approach_date": "2026-11-05",
              "orbiting_body": "Earth", "miss_distance_km": 1_000_000.0,
              "relative_velocity_kmh": 50_000.0}
    return CloseApproach(**{**values, **kwargs})


def make_history(*distances: float) -> dict:
    """History as returned by get_distance_history, one point per day."""
    points = [
        {"date": datetime(2026, 11, 1 + i), "orbiting_body": "Earth",
         "miss_distance_km": d, "relative_velocity_kmh": None}
        for i, d in enumerate(distances)
    ]
    return {"id_neo": 7, "name_neo": "Apophis", "orbiting_body": "Earth",
            "points": points, "closest": None}


@pytest.fixture
def daos():
    """Replaces the DAOs used by the service and yields (favorite_dao, neo_dao)."""
    with patch("service.favorite_service.FavoriteDao") as favorite_dao, \
            patch("service.favorite_service.NeoDao") as neo_dao:
        neo_dao.return_value.find_by_id_neo.side_effect = lambda id_neo: neos.get(id_neo)
        yield favorite_dao.return_value, neo_dao.return_value


@pytest.fixture
def history_deps():
    """Replaces what get_distance_history uses and yields
    (favorite_dao, neo_service, approach_dao). By default Apophis (7) is a favorite."""
    with patch("service.favorite_service.FavoriteDao") as favorite_dao, \
            patch("service.favorite_service.NeoService") as neo_service, \
            patch("service.favorite_service.CloseApproachDao") as approach_dao:
        favorite_dao.return_value.exists.return_value = True
        neo_service.return_value.get_by_id_neo.return_value = neos[7]
        yield favorite_dao.return_value, neo_service.return_value, approach_dao.return_value


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


# ---------------------------------------------------------------- get_distance_history
def test_distance_history_ok(history_deps):

    # GIVEN : approaches in disorder, one around Mars, one without body
    favorite_dao, _, approach_dao = history_deps
    approach_dao.find_by_id_neo.return_value = [
        make_approach(id_approach=1, approach_date="2026-12-01", miss_distance_km=2_000_000.0),
        make_approach(id_approach=2, approach_date="2026-11-01", miss_distance_km=800_000.0,
                      relative_velocity_kmh=60_000.0),
        make_approach(id_approach=3, approach_date="2026-11-15", orbiting_body="Mars"),
        make_approach(id_approach=4, orbiting_body=None),
    ]

    # WHEN
    res = FavoriteService().get_distance_history(1, 7)

    # THEN : only the Earth approaches, sorted by date, with the closest one
    assert res["id_neo"] == 7
    assert res["name_neo"] == "Apophis"
    assert res["orbiting_body"] == "Earth"
    assert [p["date"] for p in res["points"]] == [datetime(2026, 11, 1), datetime(2026, 12, 1)]
    assert [p["miss_distance_km"] for p in res["points"]] == [800_000.0, 2_000_000.0]
    assert res["points"][0]["relative_velocity_kmh"] == 60_000.0
    assert res["closest"]["miss_distance_km"] == 800_000.0
    favorite_dao.exists.assert_called_once_with(1, 7)
    approach_dao.find_by_id_neo.assert_called_once_with(7)


def test_distance_history_all_bodies(history_deps):

    # GIVEN
    _, _, approach_dao = history_deps
    approach_dao.find_by_id_neo.return_value = [
        make_approach(id_approach=1),
        make_approach(id_approach=2, orbiting_body="Mars"),
        make_approach(id_approach=3, orbiting_body=None),
    ]

    # WHEN
    res = FavoriteService().get_distance_history(1, 7, orbiting_body=None)

    # THEN
    assert res["orbiting_body"] is None
    assert len(res["points"]) == 3


def test_distance_history_body_is_case_insensitive(history_deps):

    # GIVEN
    _, _, approach_dao = history_deps
    approach_dao.find_by_id_neo.return_value = [make_approach(orbiting_body="EARTH")]

    # WHEN
    res = FavoriteService().get_distance_history(1, 7, orbiting_body="earth")

    # THEN
    assert len(res["points"]) == 1


def test_distance_history_ignores_incomplete_approaches(history_deps):

    # GIVEN : unreadable date, no date, no distance, and a valid one without velocity
    _, _, approach_dao = history_deps
    approach_dao.find_by_id_neo.return_value = [
        make_approach(id_approach=1, approach_date="not-a-date"),
        make_approach(id_approach=2, approach_date=None),
        make_approach(id_approach=3, miss_distance_km=None),
        make_approach(id_approach=4, relative_velocity_kmh=None),
    ]

    # WHEN
    res = FavoriteService().get_distance_history(1, 7)

    # THEN
    assert len(res["points"]) == 1
    assert res["points"][0]["relative_velocity_kmh"] is None


def test_distance_history_no_approach(history_deps):

    # GIVEN
    _, _, approach_dao = history_deps
    approach_dao.find_by_id_neo.return_value = []

    # WHEN
    res = FavoriteService().get_distance_history(1, 7)

    # THEN
    assert res["points"] == []
    assert res["closest"] is None


def test_distance_history_not_a_favorite(history_deps):

    # GIVEN
    favorite_dao, neo_service, approach_dao = history_deps
    favorite_dao.exists.return_value = False

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().get_distance_history(1, 7)

    assert exc.value.status_code == 404
    neo_service.get_by_id_neo.assert_not_called()
    approach_dao.find_by_id_neo.assert_not_called()


def test_distance_history_neo_not_found(history_deps):

    # GIVEN
    _, neo_service, approach_dao = history_deps
    neo_service.get_by_id_neo.return_value = None

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        FavoriteService().get_distance_history(1, 7)

    assert exc.value.status_code == 404
    approach_dao.find_by_id_neo.assert_not_called()


# ---------------------------------------------------------------- render_distance_chart
def test_render_distance_chart_ok():

    # GIVEN
    with patch.object(FavoriteService, "get_distance_history",
                      return_value=make_history(2_000_000.0, 800_000.0)) as history:

        # WHEN
        chart = FavoriteService().render_distance_chart(1, 7)

    # THEN : a real PNG image
    assert chart.startswith(b"\x89PNG")
    history.assert_called_once_with(1, 7, "Earth")


def test_render_distance_chart_no_data():

    # GIVEN
    with patch.object(FavoriteService, "get_distance_history", return_value=make_history()):

        # WHEN / THEN
        with pytest.raises(HTTPException) as exc:
            FavoriteService().render_distance_chart(1, 7)

    assert exc.value.status_code == 404


@pytest.mark.parametrize("distances, log_scale", [
    ((1_000_000.0, 5_000.0), True),
    ((1_000_000.0, 900_000.0), False),
])
def test_render_distance_chart_scale(distances, log_scale):

    # GIVEN
    with patch.object(FavoriteService, "get_distance_history",
                      return_value=make_history(*distances)), \
            patch("service.favorite_service.Figure") as figure:

        # WHEN
        FavoriteService().render_distance_chart(1, 7)

    # THEN : the log scale is only used when distances span more than two orders of magnitude
    ax = figure.return_value.subplots.return_value
    assert ax.set_yscale.called is log_scale


# ---------------------------------------------------------------- _parse_date
@pytest.mark.parametrize("value, expected", [
    ("2026-11-05", datetime(2026, 11, 5)),
    ("2026-Nov-05 12:00", datetime(2026, 11, 5, 12, 0)),
    ("2026-10-23 12:00:00", datetime(2026, 10, 23, 12, 0)),
    ("not-a-date", None),
    (None, None),
])
def test_parse_date(value, expected):

    # WHEN / THEN
    assert FavoriteService._parse_date(value) == expected