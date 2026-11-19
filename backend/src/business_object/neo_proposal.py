from datetime import datetime


class NeoProposal:
    """A change suggested by a user for one field of a NEO.

    A proposal never modifies the NEO: it is only stored so that an
    administrator can read it.
    """

    def __init__(
        self,
        id_neo: int,
        id_user: int,
        field: str,
        new_value: str,
        old_value: str | None = None,
        reason: str | None = None,
        id_proposal: int | None = None,
        created_at: datetime | None = None,
    ):
        self.id_proposal = id_proposal
        self.id_neo = id_neo
        self.id_user = id_user
        self.field = field
        self.old_value = old_value
        self.new_value = new_value
        self.reason = reason
        self.created_at = created_at

    def __repr__(self) -> str:
        return (
            f"NeoProposal(id_proposal={self.id_proposal}, id_neo={self.id_neo}, "
            f"id_user={self.id_user}, field={self.field!r}, new_value={self.new_value!r})"
        )