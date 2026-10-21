import os
import tempfile
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from business_object.neo import Neo
from service.neo_service import NeoService

router = APIRouter(prefix="/neos", tags=["NEO"])


# ---------------------------------------------------------------- schemas
class NeoIn(BaseModel):
    """Body for the creation of a custom NEO."""
    name_neo: str
    nasa_id: str | None = None
    diameter_min_m: float | None = None
    diameter_max_m: float | None = None
    absolute_magnitude: float | None = None
    is_hazardous: bool = False
    created_by_user_id: int | None = None


class NeoOut(BaseModel):
    """NEO returned by the API."""
    id_neo: int | None
    nasa_id: str | None
    name_neo: str | None
    diameter_min_m: float | None
    diameter_max_m: float | None
    absolute_magnitude: float | None
    is_hazardous: bool
    is_custom: bool
    created_by_user_id: int | None


def _to_out(neo: Neo) -> NeoOut:
    """Converts a Neo business object into its API representation."""
    return NeoOut(
        id_neo=neo.id_neo,
        nasa_id=neo.nasa_id,
        name_neo=neo.name_neo,
        diameter_min_m=neo.diameter_min_m,
        diameter_max_m=neo.diameter_max_m,
        absolute_magnitude=neo.absolute_magnitude,
        is_hazardous=neo.is_hazardous,
        is_custom=neo.is_custom,
        created_by_user_id=neo.created_by_user_id,
    )


def _criteria(
    nasa_id: str | None = Query(None, description="Exact NASA identifier"),
    name: str | None = Query(None, description="Case-insensitive substring of the name"),
    is_hazardous: bool | None = Query(None, description="Hazardous status"),
    user_id: int | None = Query(None, description="Custom NEOs created by this user"),
    min_diameter_m: float | None = Query(None, description="Lower bound on the mean diameter"),
    max_diameter_m: float | None = Query(None, description="Upper bound on the mean diameter"),
    max_magnitude: float | None = Query(None, description="Upper bound on the absolute magnitude"),
) -> dict:
    """Builds the criteria dictionary expected by NeoService.search_neos."""
    criteria = {
        "nasa_id": nasa_id,
        "name": name,
        "is_hazardous": is_hazardous,
        "user_id": user_id,
        "min_diameter_m": min_diameter_m,
        "max_diameter_m": max_diameter_m,
        "max_magnitude": max_magnitude,
    }
    return {k: v for k, v in criteria.items() if v is not None}


# ---------------------------------------------------------------- read
@router.get("", response_model=list[NeoOut])
def search_neos(
    criteria: dict = Depends(_criteria),
    sort_by: Literal["name", "diameter", "magnitude", "hazardous"] | None = None,
    descending: bool = False,
):
    """Searches NEOs from optional filters, with an optional sort."""
    service = NeoService()
    neos = service.search_neos(criteria)
    if sort_by:
        neos = service.sorting_neo_by(neos, sort_by, descending)
    return [_to_out(n) for n in neos]


@router.get("/export")
def export_neos(
    criteria: dict = Depends(_criteria),
    file_format: Literal["csv", "json"] = "csv",
):
    """Exports the NEOs matching the filters as a CSV or JSON file."""
    service = NeoService()
    neos = service.search_neos(criteria)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_format}")
    tmp.close()
    service.export(neos, tmp.name, file_format)

    return FileResponse(
        tmp.name,
        filename=f"neos.{file_format}",
        media_type="text/csv" if file_format == "csv" else "application/json",
        background=BackgroundTask(os.remove, tmp.name),
    )


@router.get("/nasa/{nasa_id}", response_model=NeoOut)
def get_neo_by_nasa_id(nasa_id: str):
    """Returns a NEO from its NASA identifier."""
    neo = NeoService().get_by_nasa_id(nasa_id)
    if neo is None:
        raise HTTPException(status_code=404, detail="NEO not found")
    return _to_out(neo)


@router.get("/{id_neo}", response_model=NeoOut)
def get_neo(id_neo: int):
    """Returns a NEO from its id."""
    neo = NeoService().get(id_neo)
    if neo is None:
        raise HTTPException(status_code=404, detail="NEO not found")
    return _to_out(neo)


# ---------------------------------------------------------------- write
@router.post("", response_model=NeoOut, status_code=201)
def create_neo(body: NeoIn):
    """Creates a custom NEO."""
    neo = Neo(
        id_neo=None,
        nasa_id=body.nasa_id or f"CUSTOM-{uuid.uuid4().hex[:8]}",
        name_neo=body.name_neo,
        diameter_min_m=body.diameter_min_m,
        diameter_max_m=body.diameter_max_m,
        absolute_magnitude=body.absolute_magnitude,
        is_hazardous=body.is_hazardous,
        is_custom=True,
        created_by_user_id=body.created_by_user_id,
    )
    return _to_out(NeoService().create(neo))


@router.delete("/{id_neo}", status_code=204)
def delete_neo(id_neo: int):
    """Deletes a NEO from its id."""
    NeoService().remove(id_neo)


# ---------------------------------------------------------------- NASA synchronisation
@router.post("/sync/feed")
def sync_feed(start_date: str, end_date: str):
    """Synchronizes the NEOs of a date window (YYYY-MM-DD, 7 days max)."""
    return NeoService().sync_nasa_data(start_date, end_date)


@router.post("/sync/page")
def sync_page(page: int = 0, size: int = 20):
    """Synchronizes one page of the full NASA catalog."""
    return NeoService().sync_page(page=page, size=size)