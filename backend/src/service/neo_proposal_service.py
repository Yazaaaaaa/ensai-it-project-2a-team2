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
        """
        Records the proposal of a user to change one field of a NEO.

        Args:
            id_user (int): ID of the user submitting the proposal.
            id_neo (int): ID of the target NEO.
            field (str): Name of the NEO attribute to propose a change for.
            new_value: Proposed new value (raw input converted to the field's type).
            reason (str | None): Optional justification provided by the user.

        Returns:
            tuple[NeoProposal, Neo]: The persisted NeoProposal and the target Neo.

        Raises:
            HTTPException: 400 if the field or the value is invalid, 404 if the NEO does
                not exist, 409 if the user already made the same proposal, or 500 on save failure.
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

        # Reject no-op proposals that match the current attribute value
        current = getattr(neo, field)
        if self._same(current, value):
            raise HTTPException(
                status_code=400, detail="The proposed value is the same as the current one"
            )

        # Normalize empty/whitespace-only reasons to None before length validation
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
        """
        Lists the proposals of a user (most recent first), each with its NEO.

        Args:
            id_user (int): ID of the user whose proposals are retrieved.

        Returns:
            list[tuple[NeoProposal, Neo]]: Pairs of (NeoProposal, Neo) for existing NEOs.
        """
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
        """
        Lists all the proposals (or those on one NEO) for an administrator.

        Args:
            admin (User): Caller user, which must have administrator privileges.
            id_neo (int | None): Optional NEO ID to filter proposals, or None for all NEOs.

        Returns:
            list[tuple[NeoProposal, Neo, User | None]]: Tuples of (proposal, neo, author_user).

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
        """
        Converts the received value to the expected type of the field.

        Args:
            field (str): Target field name from PROPOSABLE_FIELDS.
            raw: Raw input value to validate and convert.

        Returns:
            str | float | bool: Converted value matching the field type.

        Raises:
            HTTPException: 400 if the value cannot be converted or is invalid.
        """
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
        """
        Validates that a proposed diameter is non-negative and respects min <= max.

        Args:
            neo (Neo): Existing NEO providing the current opposite diameter bound.
            field (str): Field being updated ('diameter_min_m' or 'diameter_max_m').
            value (float): Proposed diameter value in meters.

        Raises:
            HTTPException: 400 if the diameter is negative or minimum exceeds maximum.
        """
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
        # Fill the missing bound from the existing NEO diameter to compare min vs. max
        low = low if low is not None else float(other)
        high = high if high is not None else float(other)
        if low > high:
            raise HTTPException(
                status_code=400,
                detail="The minimum diameter cannot exceed the maximum diameter",
            )

    @staticmethod
    def _same(current, value) -> bool:
        """
        Checks whether a proposed value is effectively equal to the current NEO value.

        Args:
            current: Current attribute value on the NEO.
            value: Newly converted proposed value.

        Returns:
            bool: True if both values are considered equal, False otherwise.
        """
        if current is None:
            return False
        if isinstance(value, (bool, str)):
            return current == value
        # Use floating-point tolerance to avoid false negatives on float conversions
        return math.isclose(float(current), value)

    @staticmethod
    def _to_text(value) -> str:
        """
        Serializes a typed field value into canonical text for storage in a proposal.

        Args:
            value: Typed value (bool, float, or str).

        Returns:
            str: String representation of the value.
        """
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
