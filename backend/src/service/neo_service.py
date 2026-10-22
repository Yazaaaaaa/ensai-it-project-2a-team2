import csv
import json

from fastapi import HTTPException

from business_object.close_approach import CloseApproach
from business_object.neo import Neo
from client.nasa_client import NasaClient
from dao.close_approach_dao import CloseApproachDao
from dao.neo_dao import NeoDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)

# Sort keys accepted by sorting_neo_by
SORT_KEYS = {
    "name": lambda n: (n.name_neo or "").lower(),
    "diameter": lambda n: (
        (n.diameter_min_m + n.diameter_max_m) / 2
        if n.diameter_min_m is not None and n.diameter_max_m is not None
        else None
    ),
    "magnitude": lambda n: n.absolute_magnitude,
    "hazardous": lambda n: n.is_hazardous,
}

EXPORT_FIELDS = [
    "id_neo", "nasa_id", "name_neo", "diameter_min_m", "diameter_max_m",
    "absolute_magnitude", "is_hazardous", "is_custom", "created_by_user_id",
]


class NeoService:
    """Service that manages NEOs and their close approaches."""

    @log
    def get_by_id_neo(self, id_neo: int) -> Neo | None:
        """Find a specific NEO by its id."""
        return NeoDao().find_by_id_neo(id_neo)

    @log
    def get_by_nasa_id(self, nasa_id: str) -> Neo | None:
        """Find a specific NEO by its NASA identifier."""
        return NeoDao().find_by_id_nasa(nasa_id)

    @log
    def create(self, neo: Neo) -> Neo:
        """Creates a NEO (or updates it if its nasa_id already exists)."""
        if not neo.name_neo:
            raise HTTPException(status_code=400, detail="A NEO must have a name")

        NeoDao().create(neo)
        return neo

    @log
    def remove(self, id_neo: int) -> bool:
        """Removes a NEO by its id."""
        if NeoDao().find_by_id_neo(id_neo) is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        return NeoDao().delete(id_neo)

    @log
    def search_neos(self, criteria: dict | None = None) -> list[Neo]:
        """Searches NEOs from a criteria dictionary."""
        criteria = criteria or {}
        dao = NeoDao()

        # Coarse filtering in SQL
        if criteria.get("nasa_id") is not None:
            neo = dao.find_by_id_nasa(criteria["nasa_id"])
            neos = [neo] if neo is not None else []
        elif criteria.get("user_id") is not None:
            neos = dao.find_all_by_id_user(criteria["user_id"])
        elif criteria.get("is_hazardous") is not None:
            neos = dao.find_by_hazardous(criteria["is_hazardous"])
        else:
            neos = dao.find_all()

        # Refined filtering in Python
        if criteria.get("name"):
            needle = criteria["name"].lower()
            neos = [n for n in neos if needle in (n.name_neo or "").lower()]

        mean_diameter = SORT_KEYS["diameter"]
        if criteria.get("min_diameter_m") is not None:
            neos = [n for n in neos
                    if mean_diameter(n) is not None
                    and mean_diameter(n) >= criteria["min_diameter_m"]]

        if criteria.get("max_diameter_m") is not None:
            neos = [n for n in neos
                    if mean_diameter(n) is not None
                    and mean_diameter(n) <= criteria["max_diameter_m"]]

        if criteria.get("max_magnitude") is not None:
            neos = [n for n in neos
                    if n.absolute_magnitude is not None
                    and n.absolute_magnitude <= criteria["max_magnitude"]]

        return neos

    @log
    def sorting_neo_by(self, neos: list[Neo], criteria: str, descending: bool = False) -> list[Neo]:
        """Sorts a list of NEOs. NEOs with a missing value are placed last."""
        if criteria not in SORT_KEYS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown sort criteria '{criteria}'. Choose from {list(SORT_KEYS)}",
            )

        key = SORT_KEYS[criteria]
        with_value = [n for n in neos if key(n) is not None]
        without_value = [n for n in neos if key(n) is None]
        return sorted(with_value, key=key, reverse=descending) + without_value

    @log
    def export(self, neos: list[Neo], path: str, file_format: str = "csv") -> str:
        """Exports a list of NEOs to a CSV or JSON file."""
        if file_format not in ("csv", "json"):
            raise HTTPException(status_code=400, detail="Unsupported format, use 'csv' or 'json'")

        rows = [{field: getattr(n, field, None) for field in EXPORT_FIELDS} for n in neos]

        if file_format == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=EXPORT_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)

        return path

    # ------------------------------------------------------------ close approaches
    @log
    def get_close_approaches(self, id_neo: int) -> list[CloseApproach]:
        """Retrieves all close approaches of a NEO."""
        if NeoDao().find_by_id_neo(id_neo) is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        return CloseApproachDao().find_by_id_neo(id_neo)

    @log
    def get_close_approaches_by_orbit(self, orbiting_body: str) -> list[CloseApproach]:
        """Retrieves all close approaches around a given body (e.g. 'Earth')."""
        return CloseApproachDao().find_by_orbit(orbiting_body)

    # ------------------------------------------------------------ NASA synchronisation
    @log
    def sync_nasa_data(self, start_date: str, end_date: str) -> dict:
        """Synchronizes the NEOs of a date window via the /feed endpoint."""
        neos = NasaClient().get_weekly_feed(start_date, end_date)
        return self._save_neos(neos)

    @log
    def sync_page(self, page: int, size: int = 20) -> dict:
        """Synchronizes one page of the full NASA catalog via the /browse endpoint."""
        neos = NasaClient().get_neos_page(page=page, size=size)
        return self._save_neos(neos)

    def _save_neos(self, neos: list[Neo]) -> dict:
        """Saves NEOs and their close approaches, and returns a summary."""
        neo_dao = NeoDao()
        approach_dao = CloseApproachDao()

        neo_count = 0
        approach_count = 0
        error_count = 0

        for neo in neos:
            try:
                neo_dao.create(neo)
                neo_count += 1

                for approach in neo.close_approaches:
                    approach.id_neo = neo.id_neo
                    approach_dao.create(approach)
                    # On vérifie si un ID a bien été assigné (nouvel insert)
                    if approach.id_approach is not None:
                        approach_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error synchronizing NEO {neo.nasa_id}: {e}")

        return {
            "status": "success",
            "synchronized_neos": neo_count,
            "synchronized_approaches": approach_count,
            "errors": error_count
        }