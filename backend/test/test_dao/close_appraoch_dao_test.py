import os
from unittest.mock import patch

import pytest

from business_object.close_approach import CloseApproach
from business_object.neo import Neo
from dao.close_approach_dao import CloseApproachDao
from dao.neo_dao import NeoDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"POSTGRES_SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


def make_neo(nasa_id: str) -> Neo:
    """Create and save a parent NEO (helper, not a test)."""
    neo = Neo(
        id_neo=None,
        nasa_id=nasa_id,
        name_neo=f"Neo {nasa_id}",
        diameter_min_m=10.0,
        diameter_max_m=20.0,
        absolute_magnitude=22.5,
        is_hazardous=False,
        is_custom=False,
        created_by_user_id=None,
    )
    NeoDao().create(neo)
    return neo


def make_approach(id_neo: int, date="2026-10-08", body="Earth", **kwargs) -> CloseApproach:
    """Build a CloseApproach with sensible defaults (helper, not a test)."""
    params = dict(
        id_approach=None,
        id_neo=id_neo,
        approach_date=date,
        orbiting_body=body,
        miss_distance_km=1_500_000.0,
        relative_velocity_kmh=45_000.0,
    )
    params.update(kwargs)
    return CloseApproach(**params)


def test_create_ok():
    """Successfully create a close approach"""

    # GIVEN
    neo = make_neo("CA_CREATE001")
    approach = make_approach(neo.id_neo)

    # WHEN
    creation_ok = CloseApproachDao().create(approach)

    # THEN
    assert creation_ok
    assert approach.id_approach


def test_create_duplicate_does_not_duplicate():
    """Creating the same approach twice does not insert a second row (ON CONFLICT DO NOTHING)"""

    # GIVEN
    # /!\ requires a UNIQUE constraint (e.g. on id_neo + approach_date + orbiting_body)
    # in init_db.sql, otherwise ON CONFLICT never triggers and this test fails
    neo = make_neo("CA_DUP001")
    CloseApproachDao().create(make_approach(neo.id_neo, date="2026-11-01"))

    # WHEN
    second = make_approach(neo.id_neo, date="2026-11-01")
    creation_ok = CloseApproachDao().create(second)

    # THEN
    assert creation_ok
    assert second.id_approach is None  # nothing returned by RETURNING on conflict
    assert len(CloseApproachDao().find_by_id_neo(neo.id_neo)) == 1


def test_find_by_id_neo_ok():
    """Find all approaches of a NEO"""

    # GIVEN
    neo = make_neo("CA_FIND001")
    CloseApproachDao().create(make_approach(neo.id_neo, date="2026-12-01", miss_distance_km=1.0))
    CloseApproachDao().create(make_approach(neo.id_neo, date="2027-01-01", miss_distance_km=2.0))

    # WHEN
    approaches = CloseApproachDao().find_by_id_neo(neo.id_neo)

    # THEN
    assert isinstance(approaches, list)
    assert len(approaches) == 2
    for a in approaches:
        assert isinstance(a, CloseApproach)
        assert a.id_neo == neo.id_neo
    assert sorted(a.miss_distance_km for a in approaches) == [1.0, 2.0]


def test_find_by_id_neo_values():
    """Fields are correctly read back from the database"""

    # GIVEN
    neo = make_neo("CA_VALUES001")
    CloseApproachDao().create(
        make_approach(
            neo.id_neo,
            date="2026-10-15",
            body="Earth",
            miss_distance_km=123456.7,
            relative_velocity_kmh=54321.0,
        )
    )

    # WHEN
    approach = CloseApproachDao().find_by_id_neo(neo.id_neo)[0]

    # THEN
    assert approach.id_approach
    assert approach.approach_date.startswith("2026-10-15")  # str(date) or str(datetime)
    assert approach.orbiting_body == "Earth"
    assert approach.miss_distance_km == pytest.approx(123456.7)
    assert approach.relative_velocity_kmh == pytest.approx(54321.0)


def test_find_by_id_neo_no_approach():
    """A NEO without approach (or an unknown id) gives an empty list"""

    # GIVEN
    neo = make_neo("CA_EMPTY001")

    # WHEN / THEN
    assert CloseApproachDao().find_by_id_neo(neo.id_neo) == []
    assert CloseApproachDao().find_by_id_neo(999999999) == []


def test_find_by_orbit_ok():
    """Find all approaches for a given orbiting body"""

    # GIVEN
    neo = make_neo("CA_ORBIT001")
    CloseApproachDao().create(make_approach(neo.id_neo, date="2026-10-20", body="TestBody"))
    CloseApproachDao().create(make_approach(neo.id_neo, date="2026-10-21", body="Mars"))

    # WHEN
    approaches = CloseApproachDao().find_by_orbit("TestBody")

    # THEN
    assert isinstance(approaches, list)
    assert len(approaches) >= 1
    for a in approaches:
        assert isinstance(a, CloseApproach)
        assert a.orbiting_body == "TestBody"
    assert neo.id_neo in [a.id_neo for a in approaches]


def test_find_by_orbit_non_existing():
    """An unknown orbiting body gives an empty list"""

    # WHEN
    approaches = CloseApproachDao().find_by_orbit("NoSuchBody")

    # THEN
    assert approaches == []