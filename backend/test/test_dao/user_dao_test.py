import pytest

from business_object.user import User
from dao.user_dao import UserDao
from utils.reset_database import ResetDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialize test data"""
    ResetDatabase().run(test_dao=True)


def make_user(email="new@test.com", token="new_token", **kwargs) -> User:
    """Build a new User (only used by create / ghost tests)."""
    params = dict(id_user=None, email=email, password_hash="hash",
                  role_user="user", token=token, created_at=None)
    params.update(kwargs)
    return User(**params)


# ---------------------------------------------------------------- create

def test_create_ok():
    """Successfully create a User"""
    user = make_user()

    assert UserDao().create(user) is True
    assert user.id_user is not None
    assert user.created_at is not None


def test_create_ko():
    """Fail to create a User (email déjà utilisé -> contrainte d'unicité)"""
    duplicate = make_user(email="alice@test.com")

    assert UserDao().create(duplicate) is False
    assert duplicate.id_user is None


# ------------------------------------------------------------- find_by_id

def test_find_by_id_ok():
    found = UserDao().find_by_id(1)

    assert isinstance(found, User)
    assert found.email == "alice@test.com"
    assert found.role_user == "user"
    assert found.token == "token_alice"


def test_find_by_id_ko():
    assert UserDao().find_by_id(999999) is None


# ---------------------------------------------------------- find_by_email

def test_find_by_email_ok():
    found = UserDao().find_by_email("admin@test.com")

    assert isinstance(found, User)
    assert found.id_user == 3
    assert found.role_user == "admin"


def test_find_by_email_ko():
    assert UserDao().find_by_email("inconnu@test.com") is None


# ---------------------------------------------------------- find_by_token

def test_find_by_token_ok():
    found = UserDao().find_by_token("token_bob")

    assert isinstance(found, User)
    assert found.id_user == 2
    assert found.email == "bob@test.com"


def test_find_by_token_ko():
    assert UserDao().find_by_token("token_inexistant") is None


# --------------------------------------------------------------- find_all

def test_find_all():
    users = UserDao().find_all()

    assert all(isinstance(u, User) for u in users)
    assert {1, 2, 3, 4, 5} <= {u.id_user for u in users}


# ----------------------------------------------------------------- update

def test_update_ok():
    """Successfully update an existing User (Bob, id 2)"""
    user = UserDao().find_by_id(2)
    user.email = "bob_updated@test.com"
    user.password_hash = "new_hash"
    user.role_user = "admin"
    user.token = "new_token_bob"

    assert UserDao().update(user) is True

    stored = UserDao().find_by_id(2)
    assert stored.email == "bob_updated@test.com"
    assert stored.password_hash == "new_hash"
    assert stored.role_user == "admin"
    assert stored.token == "new_token_bob"


def test_update_ko():
    """Fail to update a User (unknown id)"""
    assert UserDao().update(make_user(id_user=888888)) is False


# ----------------------------------------------------------------- delete

def test_delete_ok():
    """Successfully delete a User without relations (id 5)"""
    user = UserDao().find_by_id(5)

    assert UserDao().delete(user) is True
    assert UserDao().find_by_id(5) is None


def test_delete_ko():
    """Fail to delete a User (unknown id)"""
    assert UserDao().delete(make_user(id_user=888888)) is False