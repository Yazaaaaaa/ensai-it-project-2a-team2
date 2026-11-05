"""Service managing the favorite NEOs of the users and their distance history."""

import io
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException
from matplotlib.figure import Figure

from business_object.favorite import Favorite
from business_object.neo import Neo
from dao.close_approach_dao import CloseApproachDao
from dao.favorite_dao import FavoriteDao
from dao.neo_dao import NeoDao
from service.neo_service import NeoService
from utils.log_utils import get_logger, log

# Date format used by the NASA API, e.g. "2026-Oct-23 12:00"
NASA_DATE_FORMAT = "%Y-%b-%d %H:%M"

# If the largest distance is more than this many times the smallest one,
# the chart switches to a logarithmic axis to stay readable.
LOG_SCALE_RATIO = 100

logger = get_logger(__name__)


class FavoriteService:
    """Service that manages the favorite NEOs of the users."""

    @log
    def add(self, id_user: int, id_neo: int) -> tuple[Favorite, Neo]:
        """Adds a NEO to the favorites of a user.

        Args:
            id_user (int): The id of the user.
            id_neo (int): The id of the NEO to add.

        Returns:
            tuple[Favorite, Neo]: The created favorite and the corresponding NEO.

        Raises:
            HTTPException: 404 if the NEO does not exist, 409 if it is already a favorite,
                500 if the favorite could not be saved.
        """
        neo = NeoDao().find_by_id_neo(id_neo)
        if neo is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        dao = FavoriteDao()
        if dao.exists(id_user, id_neo):
            raise HTTPException(status_code=409, detail="NEO already in favorites")

        favorite = Favorite(id_user=id_user, id_neo=id_neo)
        if not dao.create(favorite):
            raise HTTPException(status_code=500, detail="The favorite could not be created")

        return favorite, neo

    @log
    def list_favorites(self, id_user: int) -> list[tuple[Favorite, Neo]]:
        """Lists the favorites of a user with their NEO, the most recent first.

        Args:
            id_user (int): The id of the user.

        Returns:
            list[tuple[Favorite, Neo]]: The favorites with their NEO (empty list if none).
        """
        neo_dao = NeoDao()
        result = []
        for favorite in FavoriteDao().find_all_by_user(id_user):
            neo = neo_dao.find_by_id_neo(favorite.id_neo)
            # A favorite whose NEO no longer exists is silently skipped
            if neo is not None:
                result.append((favorite, neo))
        return result

    @log
    def remove(self, id_user: int, id_neo: int) -> bool:
        """Removes a NEO from the favorites of a user.

        Args:
            id_user (int): The id of the user.
            id_neo (int): The id of the NEO to remove.

        Returns:
            bool: True if the favorite was deleted.

        Raises:
            HTTPException: 404 if the NEO is not in the favorites of the user.
        """
        dao = FavoriteDao()
        favorite = next((f for f in dao.find_all_by_user(id_user) if f.id_neo == id_neo), None)
        if favorite is None:
            raise HTTPException(status_code=404, detail="Favorite not found")

        return dao.delete(favorite)

    @log
    def get_distance_history(
        self, user_id: int, id_neo: int, orbiting_body: str | None = None
    ) -> dict:
        """Returns the miss distances of a favorite NEO over time, sorted by date.

        Args:
            user_id (int): The id of the user; the NEO must be in his favorites.
            id_neo (int): The id of the NEO.
            orbiting_body (str | None): Only keep approaches around this body
                (case-insensitive). None keeps all bodies.

        Returns:
            dict: The NEO id and name, the body filter, the chronological "points"
                and the "closest" point (None if there is no point).

        Raises:
            HTTPException: 404 if the NEO is not in the user's favorites or does not exist.
        """
        if not FavoriteDao().exists(user_id, id_neo):
            raise HTTPException(status_code=404, detail="This NEO is not in your favorites")

        neo = NeoService().get_by_id_neo(id_neo)
        if neo is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        points = []
        for approach in CloseApproachDao().find_by_id_neo(id_neo):
            if orbiting_body and (approach.orbiting_body or "").lower() != orbiting_body.lower():
                continue
            point = self._to_point(approach)
            if point is not None:
                points.append(point)

        points.sort(key=lambda p: p["date"])
        return {
            "id_neo": id_neo,
            "name_neo": neo.name_neo,
            "orbiting_body": orbiting_body,
            "points": points,
            "closest": min(points, key=lambda p: p["miss_distance_km"]) if points else None,
        }

    @log
    def render_distance_chart(
        self, user_id: int, id_neo: int, orbiting_body: str | None = None
    ) -> bytes:
        """Draws the distance history of a favorite NEO as a PNG chart.

        Args:
            user_id (int): The id of the user; the NEO must be in his favorites.
            id_neo (int): The id of the NEO.
            orbiting_body (str | None): Only draw approaches around this body.
                None draws all bodies.

        Returns:
            bytes: The PNG image.

        Raises:
            HTTPException: 404 if the NEO is not a favorite or has no approach data.
        """
        history = self.get_distance_history(user_id, id_neo, orbiting_body)
        points = history["points"]
        if not points:
            raise HTTPException(status_code=404, detail="No close approach data for this NEO")

        # Group the points by orbited body: one line (and one color) per body
        points_by_body = defaultdict(list)
        for point in points:
            points_by_body[point["orbiting_body"] or "Unknown"].append(point)

        # Figure (and not pyplot): no global state, safe in FastAPI's thread pool
        fig = Figure(figsize=(8, 4.5))
        ax = fig.subplots()
        for body_name in sorted(points_by_body):
            group = points_by_body[body_name]
            ax.plot(
                [p["date"] for p in group],
                [p["miss_distance_km"] for p in group],
                marker="o",
                linewidth=1.5,
                label=body_name,
            )

        # Distances can span several orders of magnitude: a log scale keeps them readable
        distances = [p["miss_distance_km"] for p in points]
        if max(distances) / max(min(distances), 1) > LOG_SCALE_RATIO:
            ax.set_yscale("log")

        ax.set_title(f"{history['name_neo']} - close approaches ({orbiting_body or 'all bodies'})")
        ax.set_xlabel("Date")
        ax.set_ylabel("Miss distance (km)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.autofmt_xdate()
        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120)
        return buffer.getvalue()

    @staticmethod
    def _to_point(approach) -> dict | None:
        """Converts a close approach into a chart point.

        Returns:
            dict | None: The point, or None (with a warning) if the date or the
                distance is missing or unreadable.
        """
        date = FavoriteService._parse_date(approach.approach_date)
        if date is None or approach.miss_distance_km is None:
            logger.warning("Close approach %s ignored (missing data)", approach.id_approach)
            return None

        velocity = approach.relative_velocity_kmh
        return {
            "date": date,
            "orbiting_body": approach.orbiting_body,
            "miss_distance_km": float(approach.miss_distance_km),
            "relative_velocity_kmh": float(velocity) if velocity is not None else None,
        }

    @staticmethod
    def _parse_date(value) -> datetime | None:
        """Parses an approach date, which may be a date object or a text.

        Tries the NASA format first, then the ISO format (e.g. "2026-10-23" or
        "2026-10-23 12:00:00").

        Returns:
            datetime | None: The parsed date, or None if no format matches.
        """
        text = str(value) if value is not None else ""
        try:
            return datetime.strptime(text, NASA_DATE_FORMAT)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
