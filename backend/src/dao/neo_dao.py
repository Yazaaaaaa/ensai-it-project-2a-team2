from business_object.neo import Neo
from business_object.close_approach import CloseApproach
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class NeoDao(metaclass=Singleton):
    """Class containing methods to access and manage NEOs in the database."""

    def _row_to_neo(self, row) -> Neo | None:
        """Helper method to convert a database row into a Neo object."""
        if not row:
            return None

        return Neo(
            id_neo=row.get("id_neo"),
            nasa_id=row.get("nasa_id"),
            name_neo=row.get("name_neo"),
            diameter_min_m=row.get("diameter_min_m"),
            diameter_max_m=row.get("diameter_max_m"),
            absolute_magnitude=row.get("absolute_magnitude"),
            is_hazardous=row.get("is_hazardous", False),
            is_custom=row.get("is_custom", False),
            created_by_user_id=row.get("created_by_user_id")
        )

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
    def create(self, neo: Neo) -> bool:
        """Inserts a new NEO record into the NEOW schema if it doesn't exist, or updates it."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_neo FROM NEOW.neo WHERE nasa_id = %(nasa_id)s;",
                        {"nasa_id": neo.nasa_id}
                    )
                    existing = cursor.fetchone()

                    if existing:
                        neo.id_neo = existing["id_neo"]
                        self.update(neo)
                    else:
                        cursor.execute(
                            """
                            INSERT INTO NEOW.neo (
                                nasa_id, name_neo, diameter_min_m, diameter_max_m, 
                                absolute_magnitude, is_hazardous, is_custom, created_by_user_id
                            )
                            VALUES (
                                %(nasa_id)s, %(name)s, %(d_min)s, %(d_max)s, 
                                %(mag)s, %(haz)s, %(cust)s, %(user_id)s
                            )
                            RETURNING id_neo;
                            """,
                            {
                                "nasa_id": neo.nasa_id,
                                "name": neo.name_neo,
                                "d_min": neo.diameter_min_m,
                                "d_max": neo.diameter_max_m,
                                "mag": neo.absolute_magnitude,
                                "haz": neo.is_hazardous,
                                "cust": neo.is_custom,
                                "user_id": neo.created_by_user_id
                            }
                        )
                        res = cursor.fetchone()
                        if res:
                            neo.id_neo = res["id_neo"]

            return True
        except Exception as e:
            logger.error(f"Error saving NEO {neo.nasa_id}: {e}")
            raise

    @log
    def find_by_id_neo(self, id_neo: int) -> Neo | None:
        """Retrieves a NEO by its primary key ID."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM NEOW.neo WHERE id_neo = %(id_neo)s;",
                        {"id_neo": id_neo}
                    )
                    row = cursor.fetchone()
                    return self._row_to_neo(row)
        except Exception as e:
            logger.error(f"Error finding NEO by id_neo {id_neo}: {e}")
            raise

    @log
    def find_close_approaches_by_id_neo(self, id_neo: int) -> list[CloseApproach]:
        """Retrieves all close approach records associated with a specific NEO ID."""
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

    @log
    def find_by_id_nasa(self, nasa_id: str) -> Neo | None:
        """Retrieves a NEO by its NASA identifier."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM NEOW.neo WHERE nasa_id = %(nasa_id)s;",
                        {"nasa_id": nasa_id}
                    )
                    row = cursor.fetchone()
                    return self._row_to_neo(row)
        except Exception as e:
            logger.error(f"Error finding NEO by nasa_id {nasa_id}: {e}")
            raise

    @log
    def find_all(self) -> list[Neo]:
        """Retrieves all NEOs from the database."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM NEOW.neo;")
                    rows = cursor.fetchall()
                    return [self._row_to_neo(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding all NEOs: {e}")
            raise

    @log
    def find_by_hazardous(self, is_hazardous: bool) -> list[Neo]:
        """Retrieves NEOs filtered by their hazardous status."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM NEOW.neo WHERE is_hazardous = %(haz)s;",
                        {"haz": is_hazardous}
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_neo(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding NEOs by hazardous status {is_hazardous}: {e}")
            raise

    @log
    def find_all_by_id_user(self, created_by_user_id: int) -> list[Neo]:
        """Retrieves all custom NEOs created by a specific user."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM NEOW.neo WHERE created_by_user_id = %(user_id)s;",
                        {"user_id": created_by_user_id}
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_neo(row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding NEOs by user id {created_by_user_id}: {e}")
            raise

    @log
    def update(self, neo: Neo) -> bool:
        """Updates an existing NEO in the database."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE NEOW.neo 
                        SET name_neo = %(name)s, 
                            diameter_min_m = %(d_min)s, 
                            diameter_max_m = %(d_max)s, 
                            absolute_magnitude = %(mag)s, 
                            is_hazardous = %(haz)s,
                            is_custom = %(cust)s,
                            created_by_user_id = %(user_id)s
                        WHERE id_neo = %(id)s;
                        """,
                        {
                            "name": neo.name_neo,
                            "d_min": neo.diameter_min_m,
                            "d_max": neo.diameter_max_m,
                            "mag": neo.absolute_magnitude,
                            "haz": neo.is_hazardous,
                            "cust": neo.is_custom,
                            "user_id": neo.created_by_user_id,
                            "id": neo.id_neo
                        }
                    )
            return True
        except Exception as e:
            logger.error(f"Error updating NEO {neo.id_neo}: {e}")
            raise

    @log
    def delete(self, id_neo: int) -> bool:
        """Deletes a NEO from the database by its ID."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM NEOW.neo WHERE id_neo = %(id_neo)s;",
                        {"id_neo": id_neo}
                    )
            return True
        except Exception as e:
            logger.error(f"Error deleting NEO {id_neo}: {e}")
            raise