from typing import Literal
from pydantic import BaseModel
from fastapi import Query

from business_object.neo import Neo
from business_object.close_approach import CloseApproach


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


class CloseApproachOut(BaseModel):
    """Close approach returned by the API."""
    id_approach: int | None
    id_neo: int | None
    approach_date: str | None
    orbiting_body: str | None
    miss_distance_km: float | None
    relative_velocity_kmh: float | None


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


def _approach_to_out(approach: CloseApproach) -> CloseApproachOut:
    """Converts a CloseApproach business object into its API representation."""
    return CloseApproachOut(
        id_approach=approach.id_approach,
        id_neo=approach.id_neo,
        approach_date=approach.approach_date,
        orbiting_body=approach.orbiting_body,
        miss_distance_km=approach.miss_distance_km,
        relative_velocity_kmh=approach.relative_velocity_kmh,
    )


def _criteria(
    nasa_id: str | None = Query(None, description="Exact NASA identifier"),
    name: str | None = Query(None, description="Case-insensitive substring of the name"),
    is_hazardous: bool | None = Query(None, description="Hazardous status"),
    user_id: int | None = Query(None, description="Custom NEOs created by this user"),
    min_diameter_m: float | None = Query(None, description="Lower bound on the mean diameter"),
    max_diameter_m: float | None = Query(None, description="Upper bound on the mean diameter"),
    max_magnitude: float | None = Query(None, description="Upper bound on the absolute magnitude"),
    orbiting_body: str | None = Query(None, description="NEOs with a close approach around this body (e.g. Earth)"),
    approach_date: str | None = Query(None, description="NEOs with a close approach on this date (e.g. YYYY-MM-DD)"),
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
        "orbiting_body": orbiting_body,
        "approach_date": approach_date,
    }
    return {k: v for k, v in criteria.items() if v is not None}