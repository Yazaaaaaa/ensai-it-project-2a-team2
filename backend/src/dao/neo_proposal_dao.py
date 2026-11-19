from business_object.neo_proposal import NeoProposal
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class NeoProposalDao(metaclass=Singleton):
    """Class containing methods to access NEO modification proposals in the database."""

    @staticmethod
    def _to_proposal(row) -> NeoProposal:
        return NeoProposal(
            id_proposal=row["id_proposal"],
            id_neo=row["id_neo"],
            id_user=row["id_user"],
            field=row["field"],
            old_value=row["old_value"],
            new_value=row["new_value"],
            reason=row["reason"],
            created_at=row["created_at"],
        )

    @log
    def create(self, proposal: NeoProposal) -> bool:
        """
        Stores a proposal.

        Args:
            proposal (NeoProposal): The proposal to persist.

        Returns:
            bool: True if the insertion is successful, False otherwise.
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO neo_proposal
                            (id_neo, id_user, field, old_value, new_value, reason)
                        VALUES
                            (%(id_neo)s, %(id_user)s, %(field)s,
                             %(old_value)s, %(new_value)s, %(reason)s)
                        RETURNING id_proposal, created_at;
                        """,
                        {
                            "id_neo": proposal.id_neo,
                            "id_user": proposal.id_user,
                            "field": proposal.field,
                            "old_value": proposal.old_value,
                            "new_value": proposal.new_value,
                            "reason": proposal.reason,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error creating proposal {proposal}: {e}")
            raise

        if res:
            proposal.id_proposal = res["id_proposal"]
            proposal.created_at = res["created_at"]
            return True
        return False

    @log
    def find_by_user(self, id_user: int) -> list[NeoProposal]:
        """Returns the proposals of a user, the most recent first."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM neo_proposal
                         WHERE id_user = %(id_user)s
                         ORDER BY created_at DESC, id_proposal DESC;
                        """,
                        {"id_user": id_user},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding proposals of user {id_user}: {e}")
            raise

        return [self._to_proposal(row) for row in rows]

    @log
    def find_all(self, id_neo: int | None = None) -> list[NeoProposal]:
        """Returns all the proposals (or those on one NEO), the most recent first."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                          FROM neo_proposal
                         WHERE (%(id_neo)s IS NULL OR id_neo = %(id_neo)s)
                         ORDER BY created_at DESC, id_proposal DESC;
                        """,
                        {"id_neo": id_neo},
                    )
                    rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding proposals (neo {id_neo}): {e}")
            raise

        return [self._to_proposal(row) for row in rows]

    @log
    def exists(self, id_user: int, id_neo: int, field: str, new_value: str) -> bool:
        """Checks whether the user already made this exact proposal."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT 1
                          FROM neo_proposal
                         WHERE id_user = %(id_user)s
                           AND id_neo = %(id_neo)s
                           AND field = %(field)s
                           AND new_value = %(new_value)s;
                        """,
                        {"id_user": id_user, "id_neo": id_neo,
                         "field": field, "new_value": new_value},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error checking proposal (user {id_user}, neo {id_neo}): {e}")
            raise

        return res is not None

    @log
    def delete(self, id_proposal: int) -> bool:
        """Deletes a proposal. True if a proposal was deleted, False otherwise."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM neo_proposal
                         WHERE id_proposal = %(id_proposal)s
                        RETURNING id_proposal;
                        """,
                        {"id_proposal": id_proposal},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error deleting proposal {id_proposal}: {e}")
            raise

        return res is not None