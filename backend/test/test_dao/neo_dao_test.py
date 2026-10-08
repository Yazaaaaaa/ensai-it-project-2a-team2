import os
from unittest.mock import patch
import pytest

from business_object.neo import Neo
from dao.neo_dao import NeoDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data and switch to test schema/database"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        
        # Optionnel mais recommandé : Insérer des données de référence fixes 
        # pour que les tests find_by_id avec des ID en dur (ex: 1, 998) fonctionnent à coup sûr.
        dao = NeoDao()
        try:
            dao.create(Neo(nasa_id="TEST_REF_1", name_neo="Asteroid 1", is_hazardous=True, is_custom=True))
            dao.create(Neo(nasa_id="TEST_REF_2", name_neo="Asteroid 2", is_hazardous=False, is_custom=True))
        except Exception:
            pass
            
        yield


def test_create_ok():
    """Successfully create a Neo"""
    # GIVEN
    neo = Neo(
        nasa_id="TEST_NEW_123",
        name_neo="New Test Asteroid",
        diameter_min_m=10.0,
        diameter_max_m=20.0,
        absolute_magnitude=22.0,
        is_hazardous=False,
        is_custom=True
    )

    # WHEN
    creation_ok = NeoDao().create(neo)

    # THEN
    assert creation_ok is True
    assert neo.id_neo is not None


def test_find_by_id_existing():
    """Find a NEO by an existing id"""
    # GIVEN
    # On s'appuie sur un ID fixe (par exemple 1, inséré lors du setup)
    id_neo = 1

    # WHEN
    neo = NeoDao().find_by_id_neo(id_neo)

    # THEN
    assert isinstance(neo, Neo)
    assert neo.id_neo == id_neo


def test_find_by_id_non_existing():
    """Find a NEO by a non-existing id"""
    # GIVEN
    id_neo = 999999999

    # WHEN
    neo = NeoDao().find_by_id_neo(id_neo)

    # THEN
    assert neo is None


def test_find_by_hazardous_ok():
    """Find all NEOs filtered by hazardous status"""
    # GIVEN
    is_hazardous = True

    # WHEN
    neos = NeoDao().find_by_hazardous(is_hazardous)

    # THEN
    assert isinstance(neos, list)
    for n in neos:
        assert isinstance(n, Neo)
        assert n.is_hazardous == is_hazardous


def test_find_all_ok():
    """Find all NEOs"""
    # WHEN
    neos = NeoDao().find_all()

    # THEN
    assert isinstance(neos, list)
    for n in neos:
        assert isinstance(n, Neo)