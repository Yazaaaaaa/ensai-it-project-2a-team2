import copy
from datetime import datetime

import pytest

from business_object.user import User
from service.user_service import UserService


class FakeUserDao:
    """DAO en mémoire. Stocke et renvoie des copies, comme le ferait une vraie base."""

    def __init__(self):
        self.users: dict[int, User] = {}
        self._next_id = 1
        self.fail_create = False
        self.fail_update = False

    def create(self, user: User) -> bool:
        if self.fail_create:
            return False
        user.id_user = self._next_id
        user.created_at = datetime.now()
        self._next_id += 1
        self.users[user.id_user] = copy.copy(user)
        return True

    def find_by_email(self, email: str) -> User | None:
        for u in self.users.values():
            if u.email == email:
                return copy.copy(u)
        return None

    def find_by_token(self, token: str) -> User | None:
        for u in self.users.values():
            if u.token is not None and u.token == token:
                return copy.copy(u)
        return None

    def update(self, user: User) -> bool:
        if self.fail_update or user.id_user not in self.users:
            return False
        self.users[user.id_user] = copy.copy(user)
        return True


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    """PBKDF2 avec 600 000 itérations est lent : on le réduit pour les tests."""
    monkeypatch.setattr("service.user_service.PBKDF2_ITERATIONS", 1000)


@pytest.fixture
def dao():
    return FakeUserDao()


@pytest.fixture
def service(dao):
    return UserService(user_dao=dao)


@pytest.fixture
def account(service):
    """Compte existant : email test@ensai.fr, mot de passe 'password123'."""
    return service.create_account("test@ensai.fr", "password123")


# ---------------------------------------------------------- create_account

def test_create_account_ok(service, dao):
    user = service.create_account("test@ensai.fr", "password123")

    assert user.id_user is not None
    assert user.email == "test@ensai.fr"
    assert user.role_user == "user"
    assert user.token is None
    assert user.id_user in dao.users


def test_create_account_normalizes_email(service):
    user = service.create_account("  Test@ENSAI.fr ", "password123")

    assert user.email == "test@ensai.fr"


def test_create_account_does_not_store_plain_password(service, dao):
    user = service.create_account("test@ensai.fr", "password123")

    stored_hash = dao.users[user.id_user].password_hash
    assert "password123" not in stored_hash
    assert stored_hash.startswith("pbkdf2_sha256$")


def test_create_account_uses_a_salt(service):
    first = service.create_account("a@ensai.fr", "password123")
    second = service.create_account("b@ensai.fr", "password123")

    assert first.password_hash != second.password_hash


def test_create_account_invalid_email(service, dao):
    with pytest.raises(ValueError):
        service.create_account("pas-un-email", "password123")

    assert dao.users == {}


def test_create_account_password_too_short(service, dao):
    with pytest.raises(ValueError):
        service.create_account("test@ensai.fr", "short")

    assert dao.users == {}


def test_create_account_email_already_used(service, account, dao):
    with pytest.raises(ValueError):
        service.create_account("test@ensai.fr", "password123")

    assert len(dao.users) == 1


def test_create_account_email_already_used_ignores_case(service, account):
    with pytest.raises(ValueError):
        service.create_account("TEST@ensai.fr", "password123")


def test_create_account_dao_failure(service, dao):
    dao.fail_create = True

    with pytest.raises(RuntimeError):
        service.create_account("test@ensai.fr", "password123")

    assert dao.users == {}


# ------------------------------------------------------------------- login

def test_login_ok(service, account, dao):
    user = service.login("test@ensai.fr", "password123")

    assert user is not None
    assert user.id_user == account.id_user
    assert user.token
    assert dao.users[user.id_user].token == user.token


def test_login_ignores_email_case_and_spaces(service, account):
    user = service.login("  TEST@ensai.fr ", "password123")

    assert user is not None
    assert user.id_user == account.id_user


def test_login_wrong_password(service, account, dao):
    assert service.login("test@ensai.fr", "mauvais_mot_de_passe") is None
    assert dao.users[account.id_user].token is None


def test_login_unknown_email(service):
    assert service.login("inconnu@ensai.fr", "password123") is None


def test_login_corrupted_hash(service, dao):
    dao.users[1] = User(id_user=1, email="test@ensai.fr", password_hash="garbage",
                        role_user="user", token=None, created_at=datetime.now())

    assert service.login("test@ensai.fr", "password123") is None


def test_login_dao_update_failure(service, account, dao):
    dao.fail_update = True

    assert service.login("test@ensai.fr", "password123") is None


def test_login_generates_a_new_token_each_time(service, account):
    first = service.login("test@ensai.fr", "password123")
    second = service.login("test@ensai.fr", "password123")

    assert first.token != second.token


# ------------------------------------------------------------------ logout

def test_logout_ok(service, account, dao):
    token = service.login("test@ensai.fr", "password123").token

    assert service.logout(token) is True
    assert dao.users[account.id_user].token is None
    assert dao.find_by_token(token) is None


def test_logout_unknown_token(service, account):
    assert service.logout("token_inexistant") is False


@pytest.mark.parametrize("token", [None, ""])
def test_logout_empty_token(service, account, token):
    assert service.logout(token) is False


def test_logout_twice(service, account):
    token = service.login("test@ensai.fr", "password123").token

    assert service.logout(token) is True
    assert service.logout(token) is False


def test_old_token_invalid_after_new_login(service, account):
    old_token = service.login("test@ensai.fr", "password123").token
    service.login("test@ensai.fr", "password123")

    assert service.logout(old_token) is False


if __name__ == "__main__":
    pytest.main([__file__])