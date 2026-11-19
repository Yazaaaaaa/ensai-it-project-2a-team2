from fastapi import APIRouter, Depends

from business_object.user import User
from controller.dependencies import get_current_user, require_admin
from schema.neo_proposal_schema import NeoProposalIn, NeoProposalOut, _proposal_to_out
from service.neo_proposal_service import NeoProposalService

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("", response_model=NeoProposalOut, status_code=201)
def create_proposal(body: NeoProposalIn, current_user: User = Depends(get_current_user)):
    """Proposes a change of one field of a NEO (the NEO itself is not modified)."""
    proposal, neo = NeoProposalService().propose(
        current_user.id_user, body.id_neo, body.field, body.new_value, body.reason
    )
    return _proposal_to_out(proposal, neo)


@router.get("/me", response_model=list[NeoProposalOut])
def list_my_proposals(current_user: User = Depends(get_current_user)):
    """Lists the proposals of the current user (most recent first)."""
    proposals = NeoProposalService().list_my_proposals(current_user.id_user)
    return [_proposal_to_out(p, n) for p, n in proposals]


@router.get("", response_model=list[NeoProposalOut])
def list_proposals(id_neo: int | None = None, admin: User = Depends(require_admin)):
    """Lists all the proposals, or those on one NEO (administrators only)."""
    proposals = NeoProposalService().list_proposals(admin, id_neo)
    return [_proposal_to_out(p, n, u) for p, n, u in proposals]