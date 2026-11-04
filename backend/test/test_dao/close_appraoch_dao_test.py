import psycopg2
import pytest

from business_object.close_approach import CloseApproach
from dao.close_approach_dao import CloseApproachDao
from dao.neo_dao import NeoDao
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


def ids(approaches: list[CloseApproach]) -> set[int]:
    """Ids of the given approaches."""
    return {a.id_approach for a in approaches}


# ---------------------------------------------------------------- create
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


def test_create_already_existing():
    """An approach already in the database is not inserted again"""

    # GIVEN : Apophis (2) already has this approach (id 3) in the test data
    approach = make_approach(2, date="2026-04-13", body="Earth")

    # WHEN
    creation_ok = CloseApproachDao().create(approach)

    # THEN : the id of the existing approach is read back
    assert not creation_ok
    assert approach.id_approach == 3
    assert len(CloseApproachDao().find_by_id_neo(2)) == 1


def test_create_ko():
    """Fail to create a close approach (unknown neo -> foreign key violation)"""

    # WHEN / THEN
    with pytest.raises(psycopg2.Error):
        CloseApproachDao().create(make_approach(999999999))


# ---------------------------------------------------------------- find_by_id_neo
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


# ---------------------------------------------------------------- find_by_orbit
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


# ---------------------------------------------------------------- find_by_approach_date
def test_find_by_approach_date_ok():
    """Find all approaches of a given day"""

    # WHEN : Apophis approaches the Earth on 2026-04-13 (approach 3)
    approaches = CloseApproachDao().find_by_approach_date("2026-04-13")

    # THEN
    assert 3 in ids(approaches)
    assert all(str(a.approach_date).startswith("2026-04-13") for a in approaches)


def test_find_by_approach_date_no_approach():
    """A day without approach gives an empty list"""

    # WHEN / THEN
    assert CloseApproachDao().find_by_approach_date("1900-01-01") == []


# ---------------------------------------------------------------- find_upcoming
def test_find_upcoming_ok():
    """Find the approaches that match every criteria"""

    # WHEN : Apophis, Earth, 2026-04-13, 31 000 km
    approaches = CloseApproachDao().find_upcoming("2026-04-13", 50_000.0, "Earth")

    # THEN
    assert 3 in ids(approaches)
    assert all(isinstance(a, CloseApproach) for a in approaches)
    assert all(a.orbiting_body == "Earth" for a in approaches)
    assert all(a.miss_distance_km <= 50_000.0 for a in approaches)
    assert all(str(a.approach_date) >= "2026-04-13" for a in approaches)


def test_find_upcoming_distance_filter():
    """The distance limit is inclusive"""

    # WHEN / THEN : approach 3 is at exactly 31 000 km
    assert 3 in ids(CloseApproachDao().find_upcoming("1900-01-01", 31_000.0, "Earth"))
    assert 3 not in ids(CloseApproachDao().find_upcoming("1900-01-01", 30_999.0, "Earth"))
    assert CloseApproachDao().find_upcoming("1900-01-01", 1.0, "Earth") == []


def test_find_upcoming_date_filter():
    """The start date is inclusive and past approaches are excluded"""

    # WHEN / THEN : approach 3 is on 2026-04-13
    assert 3 in ids(CloseApproachDao().find_upcoming("2026-04-13", 1e12, "Earth"))
    assert 3 not in ids(CloseApproachDao().find_upcoming("2026-04-14", 1e12, "Earth"))
    assert CloseApproachDao().find_upcoming("2999-01-01", 1e12, "Earth") == []


def test_find_upcoming_orbiting_body():
    """Only the approaches to the given body are returned"""

    # WHEN : only Eros approaches Mars in the test data
    approaches = CloseApproachDao().find_upcoming("1900-01-01", 1e12, "Mars")

    # THEN
    assert [a.id_neo for a in approaches] == [1]


def test_find_upcoming_min_size():
    """The size limit is inclusive and applies to the maximum diameter of the NEO"""

    # GIVEN : approach 3 belongs to Apophis (2)
    size = NeoDao().find_by_id_neo(2).diameter_max_m

    # WHEN / THEN
    assert 3 in ids(CloseApproachDao().find_upcoming("1900-01-01", 1e12, "Earth", size))
    assert 3 not in ids(CloseApproachDao().find_upcoming("1900-01-01", 1e12, "Earth", size + 1))
    assert 3 in ids(CloseApproachDao().find_upcoming("1900-01-01", 1e12, "Earth"))
    assert CloseApproachDao().find_upcoming("1900-01-01", 1e12, "Earth", 1e12) == []


# ---------------------------------------------------------------- errors
@pytest.mark.parametrize("method, args", [
    ("find_by_id_neo", ("not-a-number",)),
    ("find_by_approach_date", ("not-a-date",)),
    ("find_upcoming", ("not-a-date", 1_000_000.0, "Earth")),
])
def test_find_with_invalid_value(method, args):
    """The SQL error of an invalid value goes up"""

    # WHEN / THEN
    with pytest.raises(psycopg2.Error):
        getattr(CloseApproachDao(), method)(*args)


# ---------------------------------------------------------------- _row_to_approach
def test_row_to_approach_empty_row():
    """No row gives no approach"""

    # WHEN / THEN
    assert CloseApproachDao()._row_to_approach(None) is None


def test_row_to_approach_without_date():
    """An approach without date is read back with a date None"""

    # GIVEN : kept at the end of the file, it adds an approach to Custom Alice (4)
    CloseApproachDao().create(make_approach(4, date=None, body="Venus"))

    # WHEN
    approaches = CloseApproachDao().find_by_orbit("Venus")

    # THEN
    assert [a.approach_date for a in approaches] == [None]