import os
import tempfile
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from business_object.neo import Neo
from schema.neo_schema import (
    CloseApproachOut,
    NeoIn,
    NeoOut,
    _to_out,
    _approach_to_out,
    _criteria,
)
from service.neo_service import NeoService

router = APIRouter()

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
 

@router.get("/export", summary="Export the NEO table as CSV or JSON")
def export_neos(file_format: Literal["csv", "json"] = "csv"):
    """Downloads the whole NEO table as a CSV or JSON file."""
    content, media_type = NeoService().export_all(file_format)
    body = content.encode("utf-8-sig" if file_format == "csv" else "utf-8")
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="neos.{file_format}"'},
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
    neo = NeoService().get_by_id_neo(id_neo)
    if neo is None:
        raise HTTPException(status_code=404, detail="NEO not found")
    return _to_out(neo)
 
 
@router.get("/{id_neo}/close-approaches", response_model=list[CloseApproachOut])
def get_neo_close_approaches(id_neo: int):
    """Returns all close approaches of a NEO."""
    approaches = NeoService().get_close_approaches(id_neo)
    return [_approach_to_out(a) for a in approaches]
 
 
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
 