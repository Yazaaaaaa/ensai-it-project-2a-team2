import os
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from business_object.user import User
from dao.user_dao import UserDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    with patch.dict(os.environ, {"SCHEMA": "project_test_dao"}):
        ResetDatabase().run(test_dao=True)
        yield


def _new_user() -> User:
    """User non inséré, avec email et token uniques."""
    suffix = uuid.uuid4().hex[:8]
    return User(id_user=None, email=f"test_{suffix}@ensai.fr", password_hash="hash",
                role_user="user", token=f"tok_{suffix}", created_at=datetime.now())


@pytest.fixture
def user():
    user = _new_user()
    assert UserDao().create(user) is True
    assert user.id_user is not None
    yield user
    UserDao().delete(user)  # False si le test l'a déjà supprimé, sans conséquence


# ---------------------------------------------------------------- create

def test_create_ok():
    """Successfully create a User"""
    user = _new_user()
    try:
        assert UserDao().create(user) is True
        assert user.id_user is not None
        assert user.created_at is not None
    finally:
        if user.id_user is not None:
            UserDao().delete(user)


def test_create_ko(user):
    """Fail to create a User (email déjà utilisé -> contrainte d'unicité)"""
    duplicate = _new_user()
    duplicate.email = user.email

    assert UserDao().create(duplicate) is False
    assert duplicate.id_user is None


# ------------------------------------------------------------- find_by_id

def test_find_by_id_ok(user):
    found = UserDao().find_by_id(user.id_user)

    assert isinstance(found, User)
    assert found.id_user == user.id_user
    assert found.email == user.email
    assert found.role_user == user.role_user
    assert found.token == user.token


def test_find_by_id_ko():
    assert UserDao().find_by_id(999999) is None


# ---------------------------------------------------------- find_by_email

def test_find_by_email_ok(user):
    found = UserDao().find_by_email(user.email)

    assert isinstance(found, User)
    assert found.id_user == user.id_user


def test_find_by_email_ko():
    assert UserDao().find_by_email("inconnu@ensai.fr") is None


# ---------------------------------------------------------- find_by_token

def test_find_by_token_ok(user):
    found = UserDao().find_by_token(user.token)

    assert isinstance(found, User)
    assert found.id_user == user.id_user
    assert found.email == user.email


def test_find_by_token_ko():
    assert UserDao().find_by_token("token_inexistant") is None


# --------------------------------------------------------------- find_all

def test_find_all(user):
    users = UserDao().find_all()

    assert isinstance(users, list)
    assert all(isinstance(u, User) for u in users)
    assert user.id_user in [u.id_user for u in users]


# ----------------------------------------------------------------- update

def test_update_ok(user):
    """Successfully update an existing User"""
    suffix = uuid.uuid4().hex[:8]
    user.email = f"updated_{suffix}@ensai.fr"
    user.password_hash = "new_hash"
    user.role_user = "admin"
    user.token = f"new_tok_{suffix}"

    assert UserDao().update(user) is True

    stored = UserDao().find_by_id(user.id_user)
    assert stored.email == user.email
    assert stored.password_hash == "new_hash"
    assert stored.role_user == "admin"
    assert stored.token == user.token


def test_update_ko():
    """Fail to update a User (unknown id)"""
    ghost = _new_user()
    ghost.id_user = 888888

    assert UserDao().update(ghost) is False


# ----------------------------------------------------------------- delete

def test_delete_ok():
    """Successfully delete a User"""
    user = _new_user()
    assert UserDao().create(user) is True

    assert UserDao().delete(user) is True
    assert UserDao().find_by_id(user.id_user) is None


def test_delete_ko():
    """Fail to delete a User (unknown id)"""
    ghost = _new_user()
    ghost.id_user = 888888

    assert UserDao().delete(ghost) is False


if __name__ == "__main__":
    pytest.main([__file__])