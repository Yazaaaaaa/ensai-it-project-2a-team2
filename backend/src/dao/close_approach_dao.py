from business_object.close_approach import CloseApproach
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class CloseApproachDao(metaclass=Singleton):
    """Class containing methods to access close approaches in the database."""

    def _row_to_approach(self, row: dict | None) -> CloseApproach | None:
        """
        Helper method to convert a database row into a CloseApproach object.

        Args:
            row (dict | None): Database row returned by the cursor.

        Returns:
            CloseApproach | None: Mapped CloseApproach instance, or None if row is empty.
        """
        if not row:
            return None

        # Normalize date values (e.g., datetime.date) into strings for the business object
        approach_date = row.get("approach_date")
        if approach_date:
            approach_date = str(approach_date)

        return CloseApproach(
            id_approach=row.get("id_close_approach"),
            id_neo=row.get("id_neo"),
            approach_date=approach_date,
            orbiting_body=row.get("orbiting_body"),
            miss_distance_km=row.get("miss_distance_km"),
            relative_velocity_kmh=row.get("relative_velocity_kmh"),
        )

    @log
    def create(self, approach: CloseApproach) -> bool:
        """
        Inserts a new close approach record if it doesn't already exist.

        Args:
            approach (CloseApproach): The close approach object to persist.

        Returns:
            bool: True if a new record was inserted, False if it already existed.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    # Check uniqueness by (id_neo, orbiting_body, approach_date) before inserting
                    cursor.execute(
                        """
                        SELECT id_close_approach
                        FROM close_approach
                        WHERE id_neo = %(id_neo)s
                        AND orbiting_body = %(body)s
                        AND approach_date = %(date)s;
                        """,
                        {
                            "id_neo": approach.id_neo,
                            "body": approach.orbiting_body,
                            "date": approach.approach_date,
                        },
                    )
                    existing = cursor.fetchone()

                    # Reuse the existing ID and signal that no new row was created
                    if existing:
                        approach.id_approach = existing["id_close_approach"]
                        return False

                    cursor.execute(
                        """
                        INSERT INTO close_approach (
                            id_neo, approach_date, orbiting_body, miss_distance_km,
                            relative_velocity_kmh
                        )
                        VALUES (
                            %(id_neo)s, %(date)s, %(body)s, %(miss_dist)s, %(rel_vel)s
                        )
                        RETURNING id_close_approach;
                        """,
                        {
                            "id_neo": approach.id_neo,
                            "date": approach.approach_date,
                            "body": approach.orbiting_body,
                            "miss_dist": approach.miss_distance_km,
                            "rel_vel": approach.relative_velocity_kmh,
                        },
                    )
                    res = cursor.fetchone()
                    if res:
                        approach.id_approach = res["id_close_approach"]
            return True
        except Exception as e:
            logger.error(f"Error saving close approach for neo {approach.id_neo}: {e}")
            raise

    @log
    def find_by_id_neo(self, id_neo: int) -> list[CloseApproach]:
        """
        Retrieves all close approaches associated with a specific NEO ID.

        Args:
            id_neo (int): The ID of the Near-Earth Object.

        Returns:
            list[CloseApproach]: List of matching CloseApproach objects.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM close_approach WHERE id_neo = %(id_neo)s;",
                        {"id_neo": id_neo},
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_approach(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding close approaches for neo {id_neo}: {e}")
            raise

    @log
    def find_by_orbit(self, orbiting_body: str) -> list[CloseApproach]:
        """
        Retrieves all close approaches filtered by the orbiting body.

        Args:
            orbiting_body (str): Name of the orbiting body (e.g., 'Earth').

        Returns:
            list[CloseApproach]: List of matching CloseApproach objects.
        """
        try:
            connection = DBConnection().connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM close_approach WHERE orbiting_body = %(body)s;",
                    {"body": orbiting_body},
                )
                rows = cursor.fetchall()
                return [self._row_to_approach(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding close approaches by orbit {orbiting_body}: {e}")
            raise

    @log
    def find_by_approach_date(self, approach_date: str) -> list[CloseApproach]:
        """
        Retrieves all close approaches matching a given approach date.

        Args:
            approach_date (str): Target date formatted as YYYY-MM-DD.

        Returns:
            list[CloseApproach]: List of matching CloseApproach objects.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM close_approach
                        WHERE approach_date = %(date)s::date;
                        """,
                        {"date": approach_date},
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_approach(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding close approaches by date {approach_date}: {e}")
            raise

    @log
    def find_upcoming(
        self,
        from_date: str,
        max_km: float,
        orbiting_body: str,
        min_size_m: float | None = None,
    ) -> list[CloseApproach]:
        """
        Retrieves close approaches starting from a given date with distance and size filters.

        Args:
            from_date (str): Lower bound date formatted as YYYY-MM-DD.
            max_km (float): Maximum allowed miss distance in kilometers.
            orbiting_body (str): Name of the orbiting body (e.g., 'Earth').
            min_size_m (float | None): Minimum NEO maximum diameter in meters, or None
                to skip the size filter.

        Returns:
            list[CloseApproach]: List of close approaches matching all criteria.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT ca.*
                        FROM close_approach ca
                        JOIN neo n ON n.id_neo = ca.id_neo
                        WHERE ca.approach_date >= %(date)s::date
                        AND ca.miss_distance_km <= %(max_km)s
                        AND ca.orbiting_body = %(body)s
                        AND (%(min_size)s::float IS NULL OR n.diameter_max_m >= %(min_size)s);
                        """,
                        {
                            "date": from_date,
                            "max_km": max_km,
                            "body": orbiting_body,
                            "min_size": min_size_m,
                        },
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_approach(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding upcoming close approaches: {e}")
            raise
