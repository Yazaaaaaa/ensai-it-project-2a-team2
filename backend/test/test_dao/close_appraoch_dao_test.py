import pytest

from business_object.close_approach import CloseApproach
from dao.close_approach_dao import CloseApproachDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    ResetDatabase().run(test_dao=True)


def make_approach(id_neo: int, date="2026-11-01", body="Earth", **kwargs) -> CloseApproach:
    """Build a new CloseApproach (only used by the create tests)."""
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

    # GIVEN : Custom Alice (4) has no approach in the test data
    approach = make_approach(4, date="2026-11-01")

    # WHEN
    creation_ok = CloseApproachDao().create(approach)

    # THEN
    assert creation_ok
    assert approach.id_approach
    assert len(CloseApproachDao().find_by_id_neo(4)) == 1


def test_find_by_id_neo_ok():
    """Find all approaches of a NEO"""

    # WHEN : Eros (1) has two approaches in the test data
    approaches = CloseApproachDao().find_by_id_neo(1)

    # THEN
    assert isinstance(approaches, list)
    assert len(approaches) == 2
    assert all(isinstance(a, CloseApproach) for a in approaches)
    assert all(a.id_neo == 1 for a in approaches)
    assert sorted(a.miss_distance_km for a in approaches) == [1_000_000.0, 2_500_000.0]
    assert {a.orbiting_body for a in approaches} == {"Earth", "Mars"}


def test_find_by_id_neo_values():
    """Fields are correctly read back from the database"""

    # WHEN : Apophis (2) has a single approach
    approaches = CloseApproachDao().find_by_id_neo(2)

    # THEN
    assert len(approaches) == 1
    approach = approaches[0]
    assert approach.id_approach == 3
    assert str(approach.approach_date).startswith("2026-04-13")  # str(date) or str(datetime)
    assert approach.orbiting_body == "Earth"
    assert approach.miss_distance_km == pytest.approx(31_000.0)
    assert approach.relative_velocity_kmh == pytest.approx(60_000.0)


def test_find_by_id_neo_no_approach():
    """A NEO without approach (or an unknown id) gives an empty list"""

    # WHEN / THEN : Custom Bob (5) has no approach
    assert CloseApproachDao().find_by_id_neo(5) == []
    assert CloseApproachDao().find_by_id_neo(999999999) == []


def test_find_by_orbit_ok():
    """Find all approaches for a given orbiting body"""

    # WHEN
    approaches = CloseApproachDao().find_by_orbit("Mars")

    # THEN : only Eros approaches Mars in the test data
    assert all(isinstance(a, CloseApproach) for a in approaches)
    assert all(a.orbiting_body == "Mars" for a in approaches)
    assert [a.id_neo for a in approaches] == [1]


def test_find_by_orbit_several_neos():
    """An orbiting body shared by several NEOs returns all their approaches"""

    # WHEN
    approaches = CloseApproachDao().find_by_orbit("Earth")

    # THEN : Eros, Apophis and Bennu approach Earth in the test data
    assert {1, 2, 3} <= {a.id_neo for a in approaches}
    assert all(a.orbiting_body == "Earth" for a in approaches)


def test_find_by_orbit_non_existing():
    """An unknown orbiting body gives an empty list"""

    # WHEN
    approaches = CloseApproachDao().find_by_orbit("NoSuchBody")

    # THEN
    assert approaches == []