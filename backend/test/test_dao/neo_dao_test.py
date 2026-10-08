import os
from unittest.mock import patch

import pytest

from business_object.neo import Neo
from dao.neo_dao import NeoDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


def make_neo(nasa_id="TEST001", **kwargs) -> Neo:
    """Build a Neo with sensible defaults (helper, not a test)."""
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
    neo = make_neo("UPSERT001", name_neo="Old name")
    NeoDao().create(neo)
    first_id = neo.id_neo

    # WHEN
    neo2 = make_neo("UPSERT001", name_neo="New name")
    NeoDao().create(neo2)

    # THEN
    assert neo2.id_neo == first_id
    assert NeoDao().find_by_id_neo(first_id).name_neo == "New name"


def test_find_by_id_neo_existing():
    """Find a NEO by an existing id"""

    # GIVEN
    neo = make_neo("FINDID001")
    NeoDao().create(neo)

    # WHEN
    found = NeoDao().find_by_id_neo(neo.id_neo)

    # THEN
    assert isinstance(found, Neo)
    assert found.id_neo == neo.id_neo
    assert found.nasa_id == "FINDID001"


def test_find_by_id_neo_non_existing():
    """Find a NEO by a non-existing id"""

    # GIVEN
    id_neo = 999999999

    # WHEN
    found = NeoDao().find_by_id_neo(id_neo)

    # THEN
    assert found is None


def test_find_by_id_nasa_existing():
    """Find a NEO by an existing NASA id"""

    # GIVEN
    NeoDao().create(make_neo("NASA001"))

    # WHEN
    found = NeoDao().find_by_id_nasa("NASA001")

    # THEN
    assert isinstance(found, Neo)
    assert found.nasa_id == "NASA001"


def test_find_by_id_nasa_non_existing():
    """Find a NEO by a non-existing NASA id"""

    # WHEN
    found = NeoDao().find_by_id_nasa("DOES_NOT_EXIST")

    # THEN
    assert found is None


def test_find_all_ok():
    """Find all NEOs"""

    # GIVEN
    NeoDao().create(make_neo("ALL001"))

    # WHEN
    neos = NeoDao().find_all()

    # THEN
    assert isinstance(neos, list)
    assert len(neos) >= 1
    for n in neos:
        assert isinstance(n, Neo)


def test_find_by_hazardous_ok():
    """Find NEOs by hazardous status"""

    # GIVEN
    NeoDao().create(make_neo("HAZ001", is_hazardous=True))
    NeoDao().create(make_neo("SAFE001", is_hazardous=False))

    # WHEN
    hazardous = NeoDao().find_by_hazardous(True)
    safe = NeoDao().find_by_hazardous(False)

    # THEN
    assert "HAZ001" in [n.nasa_id for n in hazardous]
    assert all(n.is_hazardous for n in hazardous)
    assert "SAFE001" in [n.nasa_id for n in safe]
    assert all(not n.is_hazardous for n in safe)


def test_find_all_by_id_user_ok():
    """Find all custom NEOs created by a given user"""

    # GIVEN
    # /!\ id_user must exist in the users table if there is a foreign key
    id_user = 1
    NeoDao().create(make_neo("CUSTOM001", is_custom=True, created_by_user_id=id_user))

    # WHEN
    neos = NeoDao().find_all_by_id_user(id_user)

    # THEN
    assert isinstance(neos, list)
    assert "CUSTOM001" in [n.nasa_id for n in neos]
    for n in neos:
        assert n.created_by_user_id == id_user


def test_find_all_by_id_user_no_neo():
    """A user with no custom NEO gets an empty list"""

    # WHEN
    neos = NeoDao().find_all_by_id_user(987654321)

    # THEN
    assert neos == []


def test_update_ok():
    """Successfully update a NEO"""

    # GIVEN
    neo = make_neo("UPD001")
    NeoDao().create(neo)
    neo.name_neo = "Renamed"
    neo.is_hazardous = True

    # WHEN
    update_ok = NeoDao().update(neo)

    # THEN
    assert update_ok
    found = NeoDao().find_by_id_neo(neo.id_neo)
    assert found.name_neo == "Renamed"
    assert found.is_hazardous is True


def test_delete_ok():
    """Successfully delete a NEO"""

    # GIVEN
    neo = make_neo("DEL001")
    NeoDao().create(neo)

    # WHEN
    delete_ok = NeoDao().delete(neo.id_neo)

    # THEN
    assert delete_ok
    assert NeoDao().find_by_id_neo(neo.id_neo) is None