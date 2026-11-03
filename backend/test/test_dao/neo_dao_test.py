import pytest

from business_object.neo import Neo
from dao.neo_dao import NeoDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    ResetDatabase().run(test_dao=True)


def make_neo(nasa_id, **kwargs) -> Neo:
    """Build a new Neo (only used by the create tests)."""
    params = dict(
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
    params.update(kwargs)
    return Neo(**params)


def test_create_ok():
    """Successfully create a NEO"""

    # GIVEN
    neo = make_neo("CREATE001")

    # WHEN
    creation_ok = NeoDao().create(neo)

    # THEN
    assert creation_ok
    assert neo.id_neo


def test_create_existing_nasa_id_updates():
    """Creating a NEO with an already known nasa_id updates it (no duplicate)"""

    # GIVEN
    neo = make_neo("2000433", name_neo="New name")

    # WHEN
    NeoDao().create(neo)

    # THEN
    assert neo.id_neo == 1
    assert NeoDao().find_by_id_neo(1).name_neo == "New name"


def test_find_by_id_neo_existing():
    """Find a NEO by an existing id"""

    # WHEN
    found = NeoDao().find_by_id_neo(2)

    # THEN
    assert isinstance(found, Neo)
    assert found.nasa_id == "2099942"


def test_find_by_id_neo_non_existing():
    """Find a NEO by a non-existing id"""

    # WHEN
    found = NeoDao().find_by_id_neo(999999999)

    # THEN
    assert found is None


def test_find_by_id_nasa_existing():
    """Find a NEO by an existing NASA id"""

    # WHEN
    found = NeoDao().find_by_id_nasa("2101955")

    # THEN
    assert isinstance(found, Neo)
    assert found.id_neo == 3


def test_find_by_id_nasa_non_existing():
    """Find a NEO by a non-existing NASA id"""

    # WHEN
    found = NeoDao().find_by_id_nasa("DOES_NOT_EXIST")

    # THEN
    assert found is None


def test_find_all_ok():
    """Find all NEOs"""

    # WHEN
    neos = NeoDao().find_all()

    # THEN
    assert isinstance(neos, list)
    assert len(neos) >= 6
    assert all(isinstance(n, Neo) for n in neos)


def test_find_by_hazardous_ok():
    """Find NEOs by hazardous status"""

    # WHEN
    hazardous = [n.nasa_id for n in NeoDao().find_by_hazardous(True)]
    safe = [n.nasa_id for n in NeoDao().find_by_hazardous(False)]

    # THEN
    assert {"2099942", "2101955"} <= set(hazardous)
    assert "2000433" in safe
    assert not set(hazardous) & set(safe)


def test_find_all_by_id_user_ok():
    """Find all custom NEOs created by a given user"""

    # WHEN
    neos = NeoDao().find_all_by_id_user(1)

    # THEN
    assert [n.nasa_id for n in neos] == ["CUSTOM1"]


def test_find_all_by_id_user_no_neo():
    """A user with no custom NEO gets an empty list"""

    # WHEN
    neos = NeoDao().find_all_by_id_user(5)

    # THEN
    assert neos == []


def test_update_ok():
    """Successfully update a NEO"""

    # GIVEN
    neo = NeoDao().find_by_id_neo(5)
    neo.name_neo = "Renamed"
    neo.is_hazardous = True

    # WHEN
    update_ok = NeoDao().update(neo)

    # THEN
    assert update_ok
    found = NeoDao().find_by_id_neo(5)
    assert found.name_neo == "Renamed"
    assert found.is_hazardous is True


def test_delete_ok():
    """Successfully delete a NEO"""

    # WHEN
    delete_ok = NeoDao().delete(6)

    # THEN
    assert delete_ok
    assert NeoDao().find_by_id_neo(6) is None