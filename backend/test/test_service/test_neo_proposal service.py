from datetime import datetime

import pytest
from fastapi import HTTPException

from business_object.neo import Neo
from business_object.neo_proposal import NeoProposal
from business_object.user import User
from service import neo_proposal_service
from service.admin_service import ADMIN_ROLE
from service.neo_proposal_service import MAX_REASON_LENGTH, NeoProposalService


# ---------------------------------------------------------------- fakes

class FakeNeoDao:
    """In-memory NeoDao."""

    def __init__(self):
        self.neos: dict[int, Neo] = {}

    def add(self, neo: Neo) -> Neo:
        self.neos[neo.id_neo] = neo
        return neo

    def find_by_id_neo(self, id_neo: int) -> Neo | None:
        return self.neos.get(id_neo)


class FakeUserDao:
    """In-memory UserDao."""

    def __init__(self):
        self.users: dict[int, User] = {}

    def add(self, user: User) -> User:
        self.users[user.id_user] = user
        return user

    def find_by_id(self, id_user: int) -> User | None:
        return self.users.get(id_user)


class FakeNeoProposalDao:
    """In-memory NeoProposalDao. Lists are returned most recent first, like the real DAO."""

    def __init__(self):
        self.proposals: list[NeoProposal] = []
        self.fail_create = False
        self._next_id = 1

    def create(self, proposal: NeoProposal) -> bool:
        if self.fail_create:
            return False
        proposal.id_proposal = self._next_id
        proposal.created_at = datetime.now()
        self._next_id += 1
        self.proposals.append(proposal)
        return True

    def exists(self, id_user: int, id_neo: int, field: str, new_value: str) -> bool:
        return any(
            p.id_user == id_user and p.id_neo == id_neo
            and p.field == field and p.new_value == new_value
            for p in self.proposals
        )

    def find_by_user(self, id_user: int) -> list[NeoProposal]:
        return [p for p in reversed(self.proposals) if p.id_user == id_user]

    def find_all(self, id_neo: int | None = None) -> list[NeoProposal]:
        return [p for p in reversed(self.proposals) if id_neo is None or p.id_neo == id_neo]


# -------------------------------------------------------------- helpers

def _make_neo(id_neo: int = 1, **overrides) -> Neo:
    values = dict(
        id_neo=id_neo, nasa_id=f"NASA_{id_neo}", name_neo="Apophis",
        diameter_min_m=300.0, diameter_max_m=340.0, absolute_magnitude=19.7,
        is_hazardous=True, is_custom=False, created_by_user_id=None,
    )
    values.update(overrides)
    return Neo(**values)


def _make_user(id_user: int, role_user: str = "user") -> User:
    return User(id_user=id_user, email=f"user{id_user}@ensai.fr", password_hash="hash",
                role_user=role_user, token=None, created_at=datetime.now())


def assert_http_error(status_code: int, func, *args, **kwargs):
    with pytest.raises(HTTPException) as exc:
        func(*args, **kwargs)
    assert exc.value.status_code == status_code


# ------------------------------------------------------------- fixtures

@pytest.fixture
def neo_dao(monkeypatch):
    dao = FakeNeoDao()
    monkeypatch.setattr(neo_proposal_service, "NeoDao", lambda: dao)
    return dao


@pytest.fixture
def proposal_dao(monkeypatch):
    dao = FakeNeoProposalDao()
    monkeypatch.setattr(neo_proposal_service, "NeoProposalDao", lambda: dao)
    return dao


@pytest.fixture
def user_dao(monkeypatch):
    dao = FakeUserDao()
    monkeypatch.setattr(neo_proposal_service, "UserDao", lambda: dao)
    return dao


@pytest.fixture
def service(neo_dao, proposal_dao, user_dao):
    return NeoProposalService()


@pytest.fixture
def neo(neo_dao):
    """NEO 1: min diameter 300, max diameter 340, magnitude 19.7, hazardous."""
    return neo_dao.add(_make_neo(1))


# ---------------------------------------------------------------- propose: ok

def test_propose_text_field(service, neo, proposal_dao):
    proposal, returned_neo = service.propose(10, neo.id_neo, "name_neo", "  99942 Apophis ")

    assert proposal.id_proposal is not None
    assert proposal.id_user == 10
    assert proposal.id_neo == neo.id_neo
    assert proposal.field == "name_neo"
    assert proposal.old_value == "Apophis"
    assert proposal.new_value == "99942 Apophis"
    assert returned_neo is neo
    assert proposal_dao.proposals == [proposal]


@pytest.mark.parametrize("raw, expected", [
    (350.5, "350.5"),
    ("350.5", "350.5"),
    (350, "350.0"),
    ("350", "350.0"),
])
def test_propose_float_field(service, neo, raw, expected):
    proposal, _ = service.propose(10, neo.id_neo, "diameter_max_m", raw)

    assert proposal.old_value == "340.0"
    assert proposal.new_value == expected


@pytest.mark.parametrize("raw", [False, "false", "False", "0", "no"])
def test_propose_bool_field(service, neo, raw):
    proposal, _ = service.propose(10, neo.id_neo, "is_hazardous", raw)

    assert proposal.old_value == "true"
    assert proposal.new_value == "false"


def test_propose_when_current_value_is_unknown(service, neo_dao):
    neo_dao.add(_make_neo(2, absolute_magnitude=None))

    proposal, _ = service.propose(10, 2, "absolute_magnitude", 21.3)

    assert proposal.old_value is None
    assert proposal.new_value == "21.3"


def test_propose_negative_magnitude_is_accepted(service, neo):
    proposal, _ = service.propose(10, neo.id_neo, "absolute_magnitude", -1.5)

    assert proposal.new_value == "-1.5"


def test_propose_reason_is_stripped(service, neo):
    proposal, _ = service.propose(10, neo.id_neo, "name_neo", "New name", "  better data  ")

    assert proposal.reason == "better data"


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_propose_empty_reason_becomes_none(service, neo, reason):
    proposal, _ = service.propose(10, neo.id_neo, "name_neo", "New name", reason)

    assert proposal.reason is None


def test_propose_does_not_modify_the_neo(service, neo):
    service.propose(10, neo.id_neo, "diameter_max_m", 500)

    assert neo.diameter_max_m == 340.0


def test_propose_same_value_by_another_user_is_accepted(service, neo, proposal_dao):
    service.propose(10, neo.id_neo, "name_neo", "New name")
    service.propose(11, neo.id_neo, "name_neo", "New name")

    assert len(proposal_dao.proposals) == 2


# ----------------------------------------------------------- propose: errors

@pytest.mark.parametrize("field", ["nasa_id", "id_neo", "is_custom", "unknown"])
def test_propose_field_not_allowed(service, neo, proposal_dao, field):
    assert_http_error(400, service.propose, 10, neo.id_neo, field, "x")

    assert proposal_dao.proposals == []


def test_propose_unknown_neo(service, proposal_dao):
    assert_http_error(404, service.propose, 10, 999999, "name_neo", "New name")

    assert proposal_dao.proposals == []


@pytest.mark.parametrize("field, raw", [
    ("diameter_max_m", "abc"),
    ("diameter_max_m", "nan"),
    ("diameter_max_m", "inf"),
    ("diameter_max_m", True),
    ("absolute_magnitude", ""),
    ("is_hazardous", "maybe"),
    ("name_neo", "   "),
])
def test_propose_invalid_value(service, neo, proposal_dao, field, raw):
    assert_http_error(400, service.propose, 10, neo.id_neo, field, raw)

    assert proposal_dao.proposals == []


def test_propose_negative_diameter(service, neo):
    assert_http_error(400, service.propose, 10, neo.id_neo, "diameter_min_m", -1)


@pytest.mark.parametrize("field, raw", [
    ("diameter_min_m", 400),   # above the current max (340)
    ("diameter_max_m", 250),   # below the current min (300)
])
def test_propose_inconsistent_diameters(service, neo, proposal_dao, field, raw):
    assert_http_error(400, service.propose, 10, neo.id_neo, field, raw)

    assert proposal_dao.proposals == []


@pytest.mark.parametrize("field, raw", [
    ("diameter_min_m", 340),   # equal to the current max: allowed
    ("diameter_max_m", 300),   # equal to the current min: allowed
    ("diameter_min_m", 310),
    ("diameter_max_m", 500),
])
def test_propose_consistent_diameters(service, neo, field, raw):
    proposal, _ = service.propose(10, neo.id_neo, field, raw)

    assert proposal.field == field


def test_propose_diameter_when_the_other_one_is_unknown(service, neo_dao):
    neo_dao.add(_make_neo(2, diameter_max_m=None))

    proposal, _ = service.propose(10, 2, "diameter_min_m", 5000)

    assert proposal.new_value == "5000.0"


@pytest.mark.parametrize("field, raw", [
    ("name_neo", "Apophis"),
    ("diameter_min_m", 300),
    ("diameter_min_m", "300.0"),
    ("absolute_magnitude", 19.7),
    ("is_hazardous", True),
    ("is_hazardous", "true"),
])
def test_propose_same_as_current_value(service, neo, proposal_dao, field, raw):
    assert_http_error(400, service.propose, 10, neo.id_neo, field, raw)

    assert proposal_dao.proposals == []


def test_propose_reason_too_long(service, neo, proposal_dao):
    assert_http_error(400, service.propose, 10, neo.id_neo, "name_neo", "New name",
                      "x" * (MAX_REASON_LENGTH + 1))

    assert proposal_dao.proposals == []


def test_propose_reason_at_the_limit(service, neo):
    proposal, _ = service.propose(10, neo.id_neo, "name_neo", "New name", "x" * MAX_REASON_LENGTH)

    assert len(proposal.reason) == MAX_REASON_LENGTH


def test_propose_duplicate(service, neo, proposal_dao):
    service.propose(10, neo.id_neo, "diameter_max_m", 350)

    assert_http_error(409, service.propose, 10, neo.id_neo, "diameter_max_m", "350")

    assert len(proposal_dao.proposals) == 1


def test_propose_dao_failure(service, neo, proposal_dao):
    proposal_dao.fail_create = True

    assert_http_error(500, service.propose, 10, neo.id_neo, "name_neo", "New name")


# ------------------------------------------------------- list_my_proposals

def test_list_my_proposals_most_recent_first(service, neo):
    first, _ = service.propose(10, neo.id_neo, "name_neo", "Name A")
    second, _ = service.propose(10, neo.id_neo, "name_neo", "Name B")

    result = service.list_my_proposals(10)

    assert [p.id_proposal for p, _ in result] == [second.id_proposal, first.id_proposal]
    assert all(n is neo for _, n in result)


def test_list_my_proposals_only_returns_the_proposals_of_the_user(service, neo):
    mine, _ = service.propose(10, neo.id_neo, "name_neo", "Name A")
    service.propose(11, neo.id_neo, "name_neo", "Name B")

    result = service.list_my_proposals(10)

    assert [p.id_proposal for p, _ in result] == [mine.id_proposal]


def test_list_my_proposals_empty(service):
    assert service.list_my_proposals(10) == []


def test_list_my_proposals_skips_a_missing_neo(service, neo, proposal_dao):
    service.propose(10, neo.id_neo, "name_neo", "Name A")
    proposal_dao.create(NeoProposal(id_neo=999999, id_user=10, field="name_neo", new_value="x"))

    result = service.list_my_proposals(10)

    assert len(result) == 1
    assert result[0][1] is neo


# --------------------------------------------------------- list_proposals

def test_list_proposals_as_admin(service, neo, neo_dao, user_dao):
    admin = _make_user(1, ADMIN_ROLE)
    author = user_dao.add(_make_user(10))
    other_neo = neo_dao.add(_make_neo(2, name_neo="Bennu"))
    first, _ = service.propose(author.id_user, neo.id_neo, "name_neo", "Name A")
    second, _ = service.propose(author.id_user, other_neo.id_neo, "name_neo", "Name B")

    result = service.list_proposals(admin)

    assert [p.id_proposal for p, _, _ in result] == [second.id_proposal, first.id_proposal]
    assert [n for _, n, _ in result] == [other_neo, neo]
    assert all(u is author for _, _, u in result)


def test_list_proposals_filtered_by_neo(service, neo, neo_dao):
    admin = _make_user(1, ADMIN_ROLE)
    other_neo = neo_dao.add(_make_neo(2))
    service.propose(10, neo.id_neo, "name_neo", "Name A")
    wanted, _ = service.propose(10, other_neo.id_neo, "name_neo", "Name B")

    result = service.list_proposals(admin, other_neo.id_neo)

    assert [p.id_proposal for p, _, _ in result] == [wanted.id_proposal]


def test_list_proposals_unknown_proposer(service, neo):
    admin = _make_user(1, ADMIN_ROLE)
    service.propose(10, neo.id_neo, "name_neo", "Name A")  # user 10 is not in the fake DAO

    result = service.list_proposals(admin)

    assert len(result) == 1
    assert result[0][2] is None


def test_list_proposals_empty(service):
    assert service.list_proposals(_make_user(1, ADMIN_ROLE)) == []


def test_list_proposals_requires_admin(service, neo):
    service.propose(10, neo.id_neo, "name_neo", "Name A")

    assert_http_error(403, service.list_proposals, _make_user(10, "user"))


def test_list_proposals_requires_a_caller(service):
    assert_http_error(403, service.list_proposals, None)


if __name__ == "__main__":
    pytest.main([__file__])