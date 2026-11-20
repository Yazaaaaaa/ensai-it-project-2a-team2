from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from business_object.neo import Neo
from business_object.neo_proposal import NeoProposal
from business_object.user import User
from schema.neo_schema import NeoOut, _to_out


class NeoProposalIn(BaseModel):
    """Body to propose a change of one field of a NEO."""
    id_neo: int
    field: Literal[
        "name_neo", "diameter_min_m", "diameter_max_m", "absolute_magnitude", "is_hazardous"
    ]
    new_value: str | float | bool
    reason: str | None = Field(None, max_length=500)


class NeoProposalOut(BaseModel):
    """Proposal returned by the API, with the NEO it refers to."""
    id_proposal: int | None
    id_neo: int
    id_user: int
    field: str
    old_value: str | None
    new_value: str
    reason: str | None
    created_at: datetime | None
    neo: NeoOut
    proposer_email: str | None = None


def _proposal_to_out(
    proposal: NeoProposal, neo: Neo, proposer: User | None = None
) -> NeoProposalOut:
    """Converts a proposal and its NEO into their API representation."""
    return NeoProposalOut(
        id_proposal=proposal.id_proposal,
        id_neo=proposal.id_neo,
        id_user=proposal.id_user,
        field=proposal.field,
        old_value=proposal.old_value,
        new_value=proposal.new_value,
        reason=proposal.reason,
        created_at=proposal.created_at,
        neo=_to_out(neo),
        proposer_email=proposer.email if proposer else None,
    )
