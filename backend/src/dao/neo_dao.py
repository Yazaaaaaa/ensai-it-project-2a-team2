from business_object.neo import Neo
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class NeoDao(metaclass=Singleton):
    """Class containing methods to access NEOs in the database."""

    @log
    def create(self, neo: Neo) -> bool:
        """
        Inserts a new NEO record into the NEOW schema if it doesn't exist, or updates it.
        
        Args:
            neo (Neo): The NEO object to persist.
            
        Returns:
            bool: True if operation is successful.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    # Vérification si le NEO existe déjà via son nasa_id
                    cursor.execute(
                        "SELECT id_neo FROM NEOW.neo WHERE nasa_id = %(nasa_id)s;",
                        {"nasa_id": neo.nasa_id}
                    )
                    existing = cursor.fetchone()

                    if existing:
                        neo.id_neo = existing["id_neo"]
                        cursor.execute(
                            """
                            UPDATE NEOW.neo 
                            SET name_neo = %(name)s, diameter_min_m = %(d_min)s, 
                                diameter_max_m = %(d_max)s, absolute_magnitude = %(mag)s, 
                                is_hazardous = %(haz)s
                            WHERE id_neo = %(id)s;
                            """,
                            {
                                "name": neo.name_neo,
                                "d_min": neo.diameter_min_m,
                                "d_max": neo.diameter_max_m,
                                "mag": neo.absolute_magnitude,
                                "haz": neo.is_hazardous,
                                "id": neo.id_neo
                            }
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO NEOW.neo (nasa_id, name_neo, diameter_min_m, diameter_max_m, absolute_magnitude, is_hazardous, is_custom)
                            VALUES (%(nasa_id)s, %(name)s, %(d_min)s, %(d_max)s, %(mag)s, %(haz)s, FALSE)
                            RETURNING id_neo;
                            """,
                            {
                                "nasa_id": neo.nasa_id,
                                "name": neo.name_neo,
                                "d_min": neo.diameter_min_m,
                                "d_max": neo.diameter_max_m,
                                "mag": neo.absolute_magnitude,
                                "haz": neo.is_hazardous
                            }
                        )
                        res = cursor.fetchone()
                        if res:
                            neo.id_neo = res["id_neo"]

            return True
        except Exception as e:
            logger.error(f"Error saving NEO {neo.nasa_id}: {e}")
            raise