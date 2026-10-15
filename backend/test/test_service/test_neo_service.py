import csv
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from business_object.neo import Neo
from dao.neo_dao import NeoDao
from service.neo_service import NeoService

neos = [
    Neo(id_neo=1, nasa_id="2000433", name_neo="Eros", diameter_min_m=100, diameter_max_m=200,
        absolute_magnitude=10.0, is_hazardous=False, is_custom=False, created_by_user_id=None),
    Neo(id_neo=2, nasa_id="2099942", name_neo="Apophis", diameter_min_m=300, diameter_max_m=400,
        absolute_magnitude=20.0, is_hazardous=True, is_custom=False, created_by_user_id=None),
    Neo(id_neo=3, nasa_id="2101955", name_neo="Bennu", diameter_min_m=400, diameter_max_m=600,
        absolute_magnitude=21.0, is_hazardous=True, is_custom=False, created_by_user_id=None),
    Neo(id_neo=4, nasa_id="CUSTOM-1", name_neo="Custom", diameter_min_m=None, diameter_max_m=None,
        absolute_magnitude=None, is_hazardous=False, is_custom=True, created_by_user_id=7),
]


# ---------------------------------------------------------------- get
def test_get_found():

    # GIVEN
    NeoDao().find_by_id_neo = MagicMock(return_value=neos[0])

    # WHEN
    res = NeoService().get(1)

    # THEN
    assert res.name_neo == "Eros"


def test_get_not_found():

    # GIVEN
    NeoDao().find_by_id_neo = MagicMock(return_value=None)

    # WHEN
    res = NeoService().get(999)

    # THEN
    assert res is None


# ---------------------------------------------------------------- create
def test_create_ok():

    # GIVEN
    NeoDao().create = MagicMock(return_value=True)

    # WHEN
    res = NeoService().create(neos[0])

    # THEN
    assert res == neos[0]
    NeoDao().create.assert_called_once_with(neos[0])


def test_create_without_name():

    # GIVEN
    NeoDao().create = MagicMock(return_value=True)
    neo = Neo(id_neo=None, nasa_id="X", name_neo=None, diameter_min_m=None, diameter_max_m=None,
              absolute_magnitude=None, is_hazardous=False, is_custom=True, created_by_user_id=7)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        NeoService().create(neo)

    assert exc.value.status_code == 400
    NeoDao().create.assert_not_called()


# ---------------------------------------------------------------- remove
def test_remove_ok():

    # GIVEN
    NeoDao().find_by_id_neo = MagicMock(return_value=neos[0])
    NeoDao().delete = MagicMock(return_value=True)

    # WHEN
    res = NeoService().remove(1)

    # THEN
    assert res is True
    NeoDao().delete.assert_called_once_with(1)


def test_remove_not_found():

    # GIVEN
    NeoDao().find_by_id_neo = MagicMock(return_value=None)
    NeoDao().delete = MagicMock(return_value=True)

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        NeoService().remove(999)

    assert exc.value.status_code == 404
    NeoDao().delete.assert_not_called()


# ---------------------------------------------------------------- search_neos
def test_search_neos_no_criteria():

    # GIVEN
    NeoDao().find_all = MagicMock(return_value=neos)

    # WHEN
    res = NeoService().search_neos()

    # THEN
    assert len(res) == 4


def test_search_neos_hazardous():

    # GIVEN
    NeoDao().find_by_hazardous = MagicMock(return_value=[neos[1], neos[2]])

    # WHEN
    res = NeoService().search_neos({"is_hazardous": True})

    # THEN
    assert len(res) == 2
    for n in res:
        assert n.is_hazardous is True


def test_search_neos_by_user():

    # GIVEN
    NeoDao().find_all_by_id_user = MagicMock(return_value=[neos[3]])

    # WHEN
    res = NeoService().search_neos({"user_id": 7})

    # THEN
    assert len(res) == 1
    assert res[0].created_by_user_id == 7


def test_search_neos_by_name():

    # GIVEN
    NeoDao().find_all = MagicMock(return_value=neos)

    # WHEN
    res = NeoService().search_neos({"name": "benn"})

    # THEN
    assert len(res) == 1
    assert res[0].name_neo == "Bennu"


def test_search_neos_min_diameter():

    # GIVEN
    NeoDao().find_all = MagicMock(return_value=neos)

    # WHEN
    res = NeoService().search_neos({"min_diameter_m": 300})

    # THEN : Apophis (mean 350) and Bennu (mean 500), the NEO without diameter is excluded
    assert [n.name_neo for n in res] == ["Apophis", "Bennu"]


def test_search_neos_max_magnitude():

    # GIVEN
    NeoDao().find_all = MagicMock(return_value=neos)

    # WHEN
    res = NeoService().search_neos({"max_magnitude": 20})

    # THEN : Eros (10.0) and Apophis (20.0), the NEO without magnitude is excluded
    assert [n.name_neo for n in res] == ["Eros", "Apophis"]


# ---------------------------------------------------------------- sorting_neo_by
def test_sorting_neo_by_name():

    # WHEN
    res = NeoService().sorting_neo_by(neos, "name")

    # THEN
    assert [n.name_neo for n in res] == ["Apophis", "Bennu", "Custom", "Eros"]


def test_sorting_neo_by_diameter_descending_none_last():

    # WHEN
    res = NeoService().sorting_neo_by(neos, "diameter", descending=True)

    # THEN
    assert [n.name_neo for n in res] == ["Bennu", "Apophis", "Eros", "Custom"]


def test_sorting_neo_by_unknown_criteria():

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        NeoService().sorting_neo_by(neos, "color")

    assert exc.value.status_code == 400


# ---------------------------------------------------------------- export
def test_export_csv(tmp_path):

    # GIVEN
    path = str(tmp_path / "neos.csv")

    # WHEN
    res = NeoService().export(neos, path, "csv")

    # THEN
    assert res == path
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert rows[0]["name_neo"] == "Eros"


def test_export_json(tmp_path):

    # GIVEN
    path = str(tmp_path / "neos.json")

    # WHEN
    NeoService().export(neos, path, "json")

    # THEN
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 4
    assert data[1]["name_neo"] == "Apophis"


def test_export_unsupported_format(tmp_path):

    # WHEN / THEN
    with pytest.raises(HTTPException) as exc:
        NeoService().export(neos, str(tmp_path / "neos.xml"), "xml")

    assert exc.value.status_code == 400


# ---------------------------------------------------------------- synchronisation
def test_sync_nasa_data_ok():

    # GIVEN
    neo = MagicMock()
    neo.close_approaches = [MagicMock(), MagicMock()]

    with patch("service.neo_service.NasaClient") as nasa, \
            patch("service.neo_service.NeoDao") as neo_dao, \
            patch("service.neo_service.CloseApproachDao") as approach_dao:
        nasa.return_value.get_weekly_feed.return_value = [neo]
        neo_dao.return_value.create.return_value = True
        approach_dao.return_value.create.return_value = True

        # WHEN
        res = NeoService().sync_nasa_data("2026-10-01", "2026-10-07")

    # THEN
    assert res["synchronized_neos"] == 1
    assert res["synchronized_approaches"] == 2
    assert res["errors"] == 0


def test_sync_page_with_error():

    # GIVEN
    neo = MagicMock()
    neo.close_approaches = []

    with patch("service.neo_service.NasaClient") as nasa, \
            patch("service.neo_service.NeoDao") as neo_dao, \
            patch("service.neo_service.CloseApproachDao"):
        nasa.return_value.get_neos_page.return_value = [neo]
        neo_dao.return_value.create.side_effect = Exception("DB error")

        # WHEN
        res = NeoService().sync_page(page=0)

    # THEN
    assert res["synchronized_neos"] == 0
    assert res["errors"] == 1