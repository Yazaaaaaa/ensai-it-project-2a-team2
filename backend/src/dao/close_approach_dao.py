from business_object.close_approach import CloseApproach
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class CloseApproachDao(metaclass=Singleton):
    """Class containing methods to access close approaches in the database."""

    def _row_to_approach(self, row) -> CloseApproach | None:
        """Helper method to convert a database row into a CloseApproach object."""
        if not row:
            return None
        
        approach_date = row.get("approach_date")
        if approach_date:
            approach_date = str(approach_date)

        return CloseApproach(
            id_approach=row.get("id_approach"),
            id_neo=row.get("id_neo"),
            approach_date=approach_date,
            orbiting_body=row.get("orbiting_body"),
            miss_distance_km=row.get("miss_distance_km"),
            relative_velocity_kmh=row.get("relative_velocity_kmh")
        )

    @log
    def create(self, approach: CloseApproach) -> bool:
        """Inserts a new close approach record into the database."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    # Optionnel : éviter les doublons pour le même astéroïde à la même date
                    cursor.execute(
                        """
                        INSERT INTO NEOW.close_approach (
                            id_neo, approach_date, orbiting_body, miss_distance_km, relative_velocity_kmh
                        )
                        VALUES (
                            %(id_neo)s, %(date)s, %(body)s, %(miss_dist)s, %(rel_vel)s
                        )
                        ON CONFLICT DO NOTHING
                        RETURNING id_approach;
                        """,
                        {
                            "id_neo": approach.id_neo,
                            "date": approach.approach_date,
                            "body": approach.orbiting_body,
                            "miss_dist": approach.miss_distance_km,
                            "rel_vel": approach.relative_velocity_kmh
                        }
                    )
                    res = cursor.fetchone()
                    if res:
                        approach.id_approach = res["id_approach"]
            return True
        except Exception as e:
            logger.error(f"Error saving close approach for neo {approach.id_neo}: {e}")
            raise

    @log
    def find_by_id_neo(self, id_neo: int) -> list[CloseApproach]:
        """Retrieves all close approaches associated with a specific NEO ID."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM NEOW.close_approach WHERE id_neo = %(id_neo)s;",
                        {"id_neo": id_neo}
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_approach(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding close approaches for neo {id_neo}: {e}")
            raise