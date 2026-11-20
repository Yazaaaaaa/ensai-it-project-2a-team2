import os
import uuid
from datetime import datetime
from unittest.mock import patch

import psycopg2
import pytest

from business_object.neo import Neo
from business_object.neo_proposal import NeoProposal
from business_object.user import User
from dao.neo_dao import NeoDao
from dao.neo_proposal_dao import NeoProposalDao
from dao.user_dao import UserDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


# ---------------------------------------------------------------- helpers

def _create_user() -> User:
    suffix = uuid.uuid4().hex[:8]
    user = User(id_user=None, email=f"test_{suffix}@ensai.fr", password_hash="hash",
                role_user="user", token=f"tok_{suffix}", created_at=datetime.now())
    assert UserDao().create(user) is True
    assert user.id_user is not None
    return user


def _create_neo() -> Neo:
    suffix = uuid.uuid4().hex[:8]
    neo = Neo(nasa_id=f"TEST_{suffix}", name_neo=f"TEST_{suffix}",
              diameter_min_m=10, diameter_max_m=20)
    NeoDao().create(neo)
    assert neo.id_neo is not None
    return neo


def _make_proposal(user: User, neo: Neo, field: str = "diameter_max_m",
                   new_value: str = "25.0", old_value: str | None = "20",
                   reason: str | None = None) -> NeoProposal:
    return NeoProposal(id_neo=neo.id_neo, id_user=user.id_user, field=field,
                       old_value=old_value, new_value=new_value, reason=reason)


# --------------------------------------------------------------- fixtures

@pytest.fixture
def user():
    user = _create_user()
    yield user
    UserDao().delete(user)


@pytest.fixture
def other_user():
    user = _create_user()
    yield user
    UserDao().delete(user)


@pytest.fixture
def neo():
    neo = _create_neo()
    yield neo
    NeoDao().delete(neo.id_neo)


@pytest.fixture
def other_neo():
    neo = _create_neo()
    yield neo
    NeoDao().delete(neo.id_neo)


@pytest.fixture
def proposal(user, neo):
    """Proposal existing in the database. Deleted before the NEO and the user."""
    proposal = _make_proposal(user, neo, reason="more recent measurement")
    assert NeoProposalDao().create(proposal) is True
    assert proposal.id_proposal is not None
    yield proposal
    NeoProposalDao().delete(proposal.id_proposal)  # False if the test already deleted it


# ----------------------------------------------------------------- create

def test_create_ok(user, neo):
    """Successfully create a proposal"""
    proposal = _make_proposal(user, neo)
    try:
        assert NeoProposalDao().create(proposal) is True
        assert proposal.id_proposal is not None
        assert proposal.created_at is not None
    finally:
        if proposal.id_proposal is not None:
            NeoProposalDao().delete(proposal.id_proposal)


def test_create_without_old_value_and_reason(user, neo):
    """The old value and the reason are optional"""
    proposal = _make_proposal(user, neo, field="absolute_magnitude",
                              new_value="21.3", old_value=None, reason=None)
    try:
        assert NeoProposalDao().create(proposal) is True
        stored = NeoProposalDao().find_by_user(user.id_user)[0]
        assert stored.old_value is None
        assert stored.reason is None
    finally:
        if proposal.id_proposal is not None:
            NeoProposalDao().delete(proposal.id_proposal)


def test_create_ko_unknown_neo(user):
    """Fail to create a proposal (neo_id inexistant -> foreign key violation)"""
    proposal = NeoProposal(id_neo=999999, id_user=user.id_user,
                           field="name_neo", new_value="New name")

    with pytest.raises(psycopg2.Error):
        NeoProposalDao().create(proposal)

    assert proposal.id_proposal is None


def test_create_ko_unknown_user(neo):
    """Fail to create a proposal (id_user inexistant -> foreign key violation)"""
    proposal = NeoProposal(id_neo=neo.id_neo, id_user=999999,
                           field="name_neo", new_value="New name")

    with pytest.raises(psycopg2.Error):
        NeoProposalDao().create(proposal)


def test_create_ko_field_not_allowed(user, neo):
    """Fail to create a proposal (field outside the CHECK list)"""
    proposal = _make_proposal(user, neo, field="nasa_id", new_value="12345")

    with pytest.raises(psycopg2.Error):
        NeoProposalDao().create(proposal)


# ----------------------------------------------------------- find_by_user

def test_find_by_user_existing(proposal, user):
    """Retrieve the proposals of an existing user, with all their fields"""
    proposals = NeoProposalDao().find_by_user(user.id_user)

    assert len(proposals) == 1
    found = proposals[0]
    assert isinstance(found, NeoProposal)
    assert found.id_proposal == proposal.id_proposal
    assert found.id_neo == proposal.id_neo
    assert found.id_user == user.id_user
    assert found.field == "diameter_max_m"
    assert found.old_value == "20"
    assert found.new_value == "25.0"
    assert found.reason == "more recent measurement"
    assert found.created_at is not None


def test_find_by_user_empty(user):
    """Retrieve the proposals of a user who made none"""
    assert NeoProposalDao().find_by_user(user.id_user) == []


def test_find_by_user_unknown_user():
    assert NeoProposalDao().find_by_user(999999) == []


def test_find_by_user_only_returns_his_own(proposal, other_user):
    assert NeoProposalDao().find_by_user(other_user.id_user) == []


def test_find_by_user_most_recent_first(user, neo):
    first = _make_proposal(user, neo, new_value="25.0")
    second = _make_proposal(user, neo, new_value="30.0")
    try:
        assert NeoProposalDao().create(first) is True
        assert NeoProposalDao().create(second) is True

        found = NeoProposalDao().find_by_user(user.id_user)

        assert [p.id_proposal for p in found] == [second.id_proposal, first.id_proposal]
    finally:
        for p in (first, second):
            if p.id_proposal is not None:
                NeoProposalDao().delete(p.id_proposal)


# --------------------------------------------------------------- find_all

def test_find_all_contains_the_proposal(proposal):
    found = NeoProposalDao().find_all()

    assert all(isinstance(p, NeoProposal) for p in found)
    assert proposal.id_proposal in [p.id_proposal for p in found]


def test_find_all_filtered_by_neo(proposal, user, neo, other_neo):
    other = _make_proposal(user, other_neo, new_value="40.0")
    try:
        assert NeoProposalDao().create(other) is True

        on_neo = NeoProposalDao().find_all(neo.id_neo)
        on_other = NeoProposalDao().find_all(other_neo.id_neo)

        assert [p.id_proposal for p in on_neo] == [proposal.id_proposal]
        assert [p.id_proposal for p in on_other] == [other.id_proposal]
    finally:
        if other.id_proposal is not None:
            NeoProposalDao().delete(other.id_proposal)


def test_find_all_filtered_by_unknown_neo():
    assert NeoProposalDao().find_all(999999) == []


# ----------------------------------------------------------------- exists

def test_exists_true(proposal, user, neo):
    assert NeoProposalDao().exists(user.id_user, neo.id_neo, "diameter_max_m", "25.0") is True


def test_exists_false_other_value(proposal, user, neo):
    assert NeoProposalDao().exists(user.id_user, neo.id_neo, "diameter_max_m", "26.0") is False


def test_exists_false_other_field(proposal, user, neo):
    assert NeoProposalDao().exists(user.id_user, neo.id_neo, "diameter_min_m", "25.0") is False


def test_exists_false_other_user(proposal, other_user, neo):
    assert NeoProposalDao().exists(other_user.id_user, neo.id_neo, "diameter_max_m", "25.0") is False


def test_exists_false_other_neo(proposal, user, other_neo):
    assert NeoProposalDao().exists(user.id_user, other_neo.id_neo, "diameter_max_m", "25.0") is False


# ----------------------------------------------------------------- delete

def test_delete_ok(user, neo):
    """Successfully delete a proposal"""
    proposal = _make_proposal(user, neo)
    assert NeoProposalDao().create(proposal) is True

    assert NeoProposalDao().delete(proposal.id_proposal) is True

    assert NeoProposalDao().find_by_user(user.id_user) == []


def test_delete_ko():
    """Fail to delete a proposal (unknown id)"""
    assert NeoProposalDao().delete(888888) is False


# ---------------------------------------------------- foreign key cascades

def test_proposals_are_deleted_with_their_neo(user):
    neo = _create_neo()
    proposal = _make_proposal(user, neo)
    assert NeoProposalDao().create(proposal) is True

    NeoDao().delete(neo.id_neo)

    assert NeoProposalDao().find_all(neo.id_neo) == []


def test_proposals_are_deleted_with_their_user(neo):
    user = _create_user()
    proposal = _make_proposal(user, neo)
    assert NeoProposalDao().create(proposal) is True

    UserDao().delete(user)

    assert NeoProposalDao().find_by_user(user.id_user) == []


if __name__ == "__main__":
    pytest.main([__file__])