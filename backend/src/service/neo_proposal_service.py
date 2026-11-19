import math

from fastapi import HTTPException

from business_object.neo import Neo
from business_object.neo_proposal import NeoProposal
from business_object.user import User
from dao.neo_dao import NeoDao
from dao.neo_proposal_dao import NeoProposalDao
from dao.user_dao import UserDao
from service.admin_service import ADMIN_ROLE
from utils.log_utils import get_logger, log

logger = get_logger(__name__)

# Fields a user can propose to change, with the type expected for the value
PROPOSABLE_FIELDS = {
    "name_neo": str,
    "diameter_min_m": float,
    "diameter_max_m": float,
    "absolute_magnitude": float,
    "is_hazardous": bool,
}
MAX_REASON_LENGTH = 500


class NeoProposalService:
    """Service that manages the changes suggested by users for NEOs.

    A proposal never modifies a NEO: it is only recorded for the administrators.
    """

    @log
    def propose(
        self, id_user: int, id_neo: int, field: str, new_value, reason: str | None = None
    ) -> tuple[NeoProposal, Neo]:
        """Records the proposal of a user to change one field of a NEO.

        Raises:
            HTTPException: 400 if the field or the value is invalid, 404 if the NEO does
                not exist, 409 if the user already made the same proposal.
        """
        if field not in PROPOSABLE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' cannot be proposed. Choose from {list(PROPOSABLE_FIELDS)}",
            )

        neo = NeoDao().find_by_id_neo(id_neo)
        if neo is None:
            raise HTTPException(status_code=404, detail="NEO not found")

        value = self._convert(field, new_value)
        self._check_diameters(neo, field, value)

        current = getattr(neo, field)
        if self._same(current, value):
            raise HTTPException(
                status_code=400, detail="The proposed value is the same as the current one"
            )

        reason = (reason or "").strip() or None
        if reason and len(reason) > MAX_REASON_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"The reason must not exceed {MAX_REASON_LENGTH} characters",
            )

        new_text = self._to_text(value)
        dao = NeoProposalDao()
        if dao.exists(id_user, id_neo, field, new_text):
            raise HTTPException(status_code=409, detail="You already made this proposal")

        proposal = NeoProposal(
            id_neo=id_neo,
            id_user=id_user,
            field=field,
            old_value=None if current is None else self._to_text(current),
            new_value=new_text,
            reason=reason,
        )
        if not dao.create(proposal):
            raise HTTPException(status_code=500, detail="The proposal could not be saved")

        logger.info(f"User {id_user} proposed a change of {field} for NEO {id_neo}")
        return proposal, neo

    @log
    def list_my_proposals(self, id_user: int) -> list[tuple[NeoProposal, Neo]]:
        """Lists the proposals of a user (most recent first), each with its NEO."""
        neos: dict[int, Neo | None] = {}
        result = []
        for proposal in NeoProposalDao().find_by_user(id_user):
            if proposal.id_neo not in neos:
                neos[proposal.id_neo] = NeoDao().find_by_id_neo(proposal.id_neo)
            if neos[proposal.id_neo] is not None:
                result.append((proposal, neos[proposal.id_neo]))
        return result

    @log
    def list_proposals(
        self, admin: User, id_neo: int | None = None
    ) -> list[tuple[NeoProposal, Neo, User | None]]:
        """Lists all the proposals (or those on one NEO) for an administrator.

        Raises:
            HTTPException: 403 if the caller is not an administrator.
        """
        if admin is None or admin.role_user != ADMIN_ROLE:
            raise HTTPException(status_code=403, detail="Admin rights required")

        neos: dict[int, Neo | None] = {}
        users: dict[int, User | None] = {}
        result = []
        for proposal in NeoProposalDao().find_all(id_neo):
            if proposal.id_neo not in neos:
                neos[proposal.id_neo] = NeoDao().find_by_id_neo(proposal.id_neo)
            if proposal.id_user not in users:
                users[proposal.id_user] = UserDao().find_by_id(proposal.id_user)
            if neos[proposal.id_neo] is not None:
                result.append((proposal, neos[proposal.id_neo], users[proposal.id_user]))
        return result

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _convert(field: str, raw):
        """Converts the received value to the type of the field."""
        expected = PROPOSABLE_FIELDS[field]
        error = HTTPException(status_code=400, detail=f"Invalid value for '{field}'")
        try:
            if expected is bool:
                if isinstance(raw, bool):
                    return raw
                text = str(raw).strip().lower()
                if text in ("true", "1", "yes"):
                    return True
                if text in ("false", "0", "no"):
                    return False
                raise error
            if expected is float:
                if isinstance(raw, bool):
                    raise error
                value = float(raw)
                if not math.isfinite(value):
                    raise error
                return value
            text = str(raw).strip()
            if not text:
                raise error
            return text
        except (TypeError, ValueError):
            raise error

    @staticmethod
    def _check_diameters(neo: Neo, field: str, value) -> None:
        """A diameter cannot be negative, and the minimum cannot exceed the maximum."""
        if field not in ("diameter_min_m", "diameter_max_m"):
            return
        if value < 0:
            raise HTTPException(status_code=400, detail="A diameter cannot be negative")
        if field == "diameter_min_m":
            other, low, high = neo.diameter_max_m, value, None
        else:
            other, low, high = neo.diameter_min_m, None, value
        if other is None:
            return
        low = low if low is not None else float(other)
        high = high if high is not None else float(other)
        if low > high:
            raise HTTPException(
                status_code=400,
                detail="The minimum diameter cannot exceed the maximum diameter",
            )

    @staticmethod
    def _same(current, value) -> bool:
        if current is None:
            return False
        if isinstance(value, (bool, str)):
            return current == value
        return math.isclose(float(current), value)

    @staticmethod
    def _to_text(value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)