"""Service managing NEOs: search, sort, export, close approaches and NASA synchronisation."""

import csv
import io
import json

from fastapi import HTTPException

from business_object.close_approach import CloseApproach
from business_object.neo import Neo
from client.nasa_client import NasaClient
from dao.close_approach_dao import CloseApproachDao
from dao.neo_dao import NeoDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


def _mean_diameter(neo: Neo) -> float | None:
    """
    Returns the mean of the min and max diameters, or None if one of them is missing.

    Args:
        neo (Neo): NEO object whose diameter bounds are averaged.

    Returns:
        float | None: Average diameter in meters, or None if either bound is None.
    """
    if neo.diameter_min_m is None or neo.diameter_max_m is None:
        return None
    return (neo.diameter_min_m + neo.diameter_max_m) / 2


def _is_between(value: float | None, low: float | None = None, high: float | None = None) -> bool:
    """
    Tells whether a value lies within optional inclusive bounds (False if value is None).

    Args:
        value (float | None): Candidate numeric value to check.
        low (float | None): Optional inclusive lower bound.
        high (float | None): Optional inclusive upper bound.

    Returns:
        bool: True if value is present and within [low, high], False otherwise.
    """
    if value is None:
        return False
    return (low is None or value >= low) and (high is None or value <= high)


SORT_KEYS = {
    "name": lambda n: (n.name_neo or "").lower(),
    "diameter": _mean_diameter,
    "magnitude": lambda n: n.absolute_magnitude,
    "hazardous": lambda n: n.is_hazardous,
}

EXPORT_FIELDS = [
    "id_neo", "nasa_id", "name_neo", "diameter_min_m", "diameter_max_m",
    "absolute_magnitude", "is_hazardous", "is_custom", "created_by_user_id",
]

EXPORT_FORMATS = {
    "csv": "text/csv; charset=utf-8",
    "json": "application/json",
}

EARTH = "Earth"


class NeoService:
    """Service that manages NEOs and their close approaches."""

    # ------------------------------------------------------------ NEO CRUD

    @log
    def get_by_id_neo(self, id_neo: int) -> Neo | None:
        """
        Finds a NEO by its id (None if it does not exist).

        Args:
            id_neo (int): Primary key ID of the NEO.

        Returns:
            Neo | None: Matching Neo object, or None if not found.
        """
        return NeoDao().find_by_id_neo(id_neo)

    @log
    def get_by_nasa_id(self, nasa_id: str) -> Neo | None:
        """
        Finds a NEO by its NASA identifier (None if it does not exist).

        Args:
            nasa_id (str): NASA identifier of the NEO.

        Returns:
            Neo | None: Matching Neo object, or None if not found.
        """
        return NeoDao().find_by_id_nasa(nasa_id)

    @log
    def create(self, neo: Neo) -> Neo:
        """
        Creates a NEO (or updates it if its nasa_id already exists).

        Args:
            neo (Neo): NEO object to create or update.

        Returns:
            Neo: Saved NEO object (with id_neo populated).

        Raises:
            HTTPException: 400 if the NEO has no name.
        """
        if not neo.name_neo:
            raise HTTPException(status_code=400, detail="A NEO must have a name")

        NeoDao().create(neo)
        return neo

    @log
    def remove(self, id_neo: int) -> bool:
        """
        Removes a NEO by its id.

        Args:
            id_neo (int): Primary key ID of the NEO to remove.

        Returns:
            bool: True if the NEO was deleted.

        Raises:
            HTTPException: 404 if the NEO does not exist.
        """
        dao = NeoDao()
        if dao.find_by_id_neo(id_neo) is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        return dao.delete(id_neo)

    # ------------------------------------------------------------ search, sort, export

    @log
    def search_neos(self, criteria: dict | None = None) -> list[Neo]:
        """Searches NEOs from a criteria dictionary. All criteria are combined (AND).

        Args:
            criteria (dict, optional): Supported keys, all optional:
                nasa_id (str): exact NASA identifier of the NEO.
                name (str): case-insensitive substring of the NEO name.
                is_hazardous (bool): hazardous status.
                user_id (int): custom NEOs created by this user.
                orbiting_body (str): NEOs with a close approach around this body
                    (e.g. 'Earth'), case-sensitive.
                approach_date (str): NEOs with a close approach on this date
                    (e.g. '2026-10-23').
                min_diameter_m (float): lower bound on the mean diameter.
                max_diameter_m (float): upper bound on the mean diameter.
                max_magnitude (float): upper bound on the absolute magnitude.

        Returns:
            list[Neo]: all NEOs matching the criteria.
        """
        criteria = criteria or {}
        dao = NeoDao()

        # Pick the most selective indexed query first to narrow down candidate NEOs
        if criteria.get("nasa_id") is not None:
            neo = dao.find_by_id_nasa(criteria["nasa_id"])
            neos = [neo] if neo is not None else []
        elif criteria.get("user_id") is not None:
            neos = dao.find_all_by_id_user(criteria["user_id"])
        elif criteria.get("is_hazardous") is not None:
            neos = dao.find_by_hazardous(criteria["is_hazardous"])
        else:
            neos = dao.find_all()

        # Re-apply remaining filters in memory when another branch was chosen first
        if criteria.get("user_id") is not None:
            neos = [n for n in neos if n.created_by_user_id == criteria["user_id"]]

        if criteria.get("is_hazardous") is not None:
            neos = [n for n in neos if n.is_hazardous == criteria["is_hazardous"]]

        if criteria.get("orbiting_body"):
            approaches = CloseApproachDao().find_by_orbit(criteria["orbiting_body"])
            neos = self._keep_with_approach(neos, approaches)

        if criteria.get("approach_date"):
            approaches = CloseApproachDao().find_by_approach_date(criteria["approach_date"])
            neos = self._keep_with_approach(neos, approaches)

        if criteria.get("name"):
            needle = criteria["name"].lower()
            neos = [n for n in neos if needle in (n.name_neo or "").lower()]

        min_diameter = criteria.get("min_diameter_m")
        max_diameter = criteria.get("max_diameter_m")
        if min_diameter is not None or max_diameter is not None:
            neos = [n for n in neos if _is_between(_mean_diameter(n), min_diameter, max_diameter)]

        max_magnitude = criteria.get("max_magnitude")
        if max_magnitude is not None:
            neos = [n for n in neos if _is_between(n.absolute_magnitude, high=max_magnitude)]

        return neos

    @log
    def sorting_neo_by(
        self, neos: list[Neo], criteria: str, descending: bool = False
    ) -> list[Neo]:
        """
        Sorts a list of NEOs. NEOs with a missing value are placed last.

        Args:
            neos (list[Neo]): List of NEOs to sort.
            criteria (str): Sort key name from SORT_KEYS ('name', 'diameter',
                'magnitude', 'hazardous').
            descending (bool): Whether to sort in descending order.

        Returns:
            list[Neo]: Sorted list with missing-value items appended at the end.

        Raises:
            HTTPException: 400 if the sort criteria is unknown.
        """
        if criteria not in SORT_KEYS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown sort criteria '{criteria}'. Choose from {list(SORT_KEYS)}",
            )

        key = SORT_KEYS[criteria]
        # Separate None sort keys so they always stay at the end regardless of reverse order
        with_value = [n for n in neos if key(n) is not None]
        without_value = [n for n in neos if key(n) is None]
        return sorted(with_value, key=key, reverse=descending) + without_value

    @log
    def export_content(self, neos: list[Neo], file_format: str = "csv") -> tuple[str, str]:
        """
        Serialises NEOs to a CSV or JSON string.

        Args:
            neos (list[Neo]): List of NEOs to serialize.
            file_format (str): Target export format ('csv' or 'json').

        Returns:
            tuple[str, str]: Serialized content string and its HTTP media type.

        Raises:
            HTTPException: 400 if the format is not supported.
        """
        if file_format not in EXPORT_FORMATS:
            raise HTTPException(status_code=400, detail="Unsupported format, use 'csv' or 'json'")

        rows = [{field: getattr(n, field, None) for field in EXPORT_FIELDS} for n in neos]

        if file_format == "csv":
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            content = buffer.getvalue()
        else:
            content = json.dumps(rows, ensure_ascii=False, indent=2, default=str)

        return content, EXPORT_FORMATS[file_format]

    @log
    def export_all(self, file_format: str = "csv") -> tuple[str, str]:
        """
        Exports the whole neo table (same return value as export_content).

        Args:
            file_format (str): Target export format ('csv' or 'json').

        Returns:
            tuple[str, str]: Serialized content string and its HTTP media type.
        """
        return self.export_content(NeoDao().find_all(), file_format)

    @log
    def export(self, neos: list[Neo], path: str, file_format: str = "csv") -> str:
        """
        Exports a list of NEOs to a CSV or JSON file (local use, e.g. scripts).

        Args:
            neos (list[Neo]): List of NEOs to write out.
            path (str): Destination file path.
            file_format (str): Target export format ('csv' or 'json').

        Returns:
            str: The path of the written file.
        """
        content, _ = self.export_content(neos, file_format)
        # UTF-8 with BOM helps spreadsheet tools open CSV files without accent corruption
        encoding = "utf-8-sig" if file_format == "csv" else "utf-8"
        with open(path, "w", newline="", encoding=encoding) as file:
            file.write(content)
        return path

    # ------------------------------------------------------------ close approaches

    @log
    def get_close_approaches(self, id_neo: int) -> list[CloseApproach]:
        """
        Retrieves all close approaches of a NEO.

        Args:
            id_neo (int): Primary key ID of the NEO.

        Returns:
            list[CloseApproach]: List of close approaches for the NEO.

        Raises:
            HTTPException: 404 if the NEO does not exist.
        """
        if NeoDao().find_by_id_neo(id_neo) is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        return CloseApproachDao().find_by_id_neo(id_neo)

    @log
    def compare(self, ids: list[int]) -> list[tuple[Neo, CloseApproach | None]]:
        """
        Compares NEOs: each one comes with its closest approach to the Earth
        (None if it has none).

        Args:
            ids (list[int]): Ordered list of NEO primary key IDs to compare.

        Returns:
            list[tuple[Neo, CloseApproach | None]]: Pairs of (Neo, closest Earth approach or None).

        Raises:
            HTTPException: 404 if one of the NEOs does not exist.
        """
        result = []
        for id_neo in ids:
            neo = self.get_by_id_neo(id_neo)
            if neo is None:
                raise HTTPException(status_code=404, detail=f"NEO {id_neo} not found")
            earth_approaches = [
                a for a in CloseApproachDao().find_by_id_neo(id_neo)
                if a.orbiting_body == EARTH and a.miss_distance_km is not None
            ]
            # Pick the close approach with the smallest miss distance to Earth
            result.append((neo, min(earth_approaches, key=lambda a: a.miss_distance_km,
                                    default=None)))
        return result

    # ------------------------------------------------------------ NASA synchronisation

    @log
    def sync_nasa_data(self, start_date: str, end_date: str) -> dict:
        """
        Synchronizes the NEOs of a date window via the NASA /feed endpoint.

        Args:
            start_date (str): Start date of the window (YYYY-MM-DD).
            end_date (str): End date of the window (YYYY-MM-DD).

        Returns:
            dict: Synchronization summary counts (status, synchronized_neos,
                synchronized_approaches, errors).
        """
        neos = NasaClient().get_weekly_feed(start_date, end_date)
        return self._save_neos(neos)

    @log
    def sync_page(self, page: int, size: int = 20) -> dict:
        """
        Synchronizes one page of the full NASA catalog via the /browse endpoint.

        Args:
            page (int): Zero-based catalog page index to fetch.
            size (int): Number of NEOs per page.

        Returns:
            dict: Synchronization summary counts (status, synchronized_neos,
                synchronized_approaches, errors).
        """
        neos = NasaClient().get_neos_page(page=page, size=size)
        return self._save_neos(neos)

    # ------------------------------------------------------------ private helpers

    @staticmethod
    def _keep_with_approach(neos: list[Neo], approaches: list[CloseApproach]) -> list[Neo]:
        """
        Keeps only the NEOs that appear in the given close approaches.

        Args:
            neos (list[Neo]): Candidate NEO list to filter.
            approaches (list[CloseApproach]): Matching close approach records.

        Returns:
            list[Neo]: Filtered list of NEOs having at least one matching approach.
        """
        ids_with_approach = {a.id_neo for a in approaches}
        return [n for n in neos if n.id_neo in ids_with_approach]

    @staticmethod
    def _save_neos(neos: list[Neo]) -> dict:
        """
        Saves NEOs and their close approaches, and returns a summary.

        Args:
            neos (list[Neo]): NEO objects (with nested close_approaches) to persist.

        Returns:
            dict: Summary dictionary with counts of synced NEOs, approaches, and errors.
        """
        neo_dao = NeoDao()
        approach_dao = CloseApproachDao()

        neo_count = 0
        approach_count = 0
        error_count = 0

        for neo in neos:
            # Isolate per-NEO failures so one bad record does not abort the whole batch
            try:
                neo_dao.create(neo)
                neo_count += 1

                for approach in neo.close_approaches:
                    approach.id_neo = neo.id_neo
                    if approach_dao.create(approach):
                        approach_count += 1

            except Exception as error:
                error_count += 1
                logger.error("Error synchronizing NEO %s: %s", neo.nasa_id, error)

        return {
            "status": "success",
            "synchronized_neos": neo_count,
            "synchronized_approaches": approach_count,
            "errors": error_count,
        }
