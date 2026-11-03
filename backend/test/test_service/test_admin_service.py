import copy
import subprocess
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from business_object.user import User
from service import admin_service
from service.admin_service import AdminService


class FakeUserDao:
    """DAO en mémoire. Stocke et renvoie des copies, comme le ferait une vraie base."""

    def __init__(self):
        self.users: dict[int, User] = {}
        self.fail_update = False

    def add(self, user: User) -> User:
        self.users[user.id_user] = copy.copy(user)
        return user

    def find_by_id(self, id_user: int) -> User | None:
        user = self.users.get(id_user)
        return copy.copy(user) if user else None

    def update(self, user: User) -> bool:
        if self.fail_update or user.id_user not in self.users:
            return False
        self.users[user.id_user] = copy.copy(user)
        return True


def _make_user(id_user: int, role_user: str = "user", token: str | None = None) -> User:
    return User(id_user=id_user, email=f"user{id_user}@ensai.fr", password_hash="hash",
                role_user=role_user, token=token, created_at=datetime.now())


@pytest.fixture
def dao():
    return FakeUserDao()


@pytest.fixture
def service(dao):
    return AdminService(user_dao=dao)


@pytest.fixture
def admin(dao):
    return dao.add(_make_user(1, role_user="admin", token="admin_tok"))


@pytest.fixture
def regular_user(dao):
    return dao.add(_make_user(2, token="user_tok"))


@pytest.fixture(autouse=True)
def release_import_lock():
    """Le verrou est un attribut de classe : on garantit qu'il est libre entre les tests."""
    yield
    if AdminService._import_lock.locked():
        AdminService._import_lock.release()


@pytest.fixture
def fake_run(monkeypatch):
    """Remplace subprocess.run : aucun processus n'est lancé."""
    run = MagicMock(return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout="import ok", stderr=""))
    monkeypatch.setattr(admin_service.subprocess, "run", run)
    return run


# ---------------------------------------------------------------- ban_user

def test_ban_user_ok(service, admin, regular_user, dao):
    assert service.ban_user(admin, regular_user.id_user) is True

    stored = dao.users[regular_user.id_user]
    assert stored.is_banned is True


def test_ban_user_closes_current_session(service, admin, regular_user, dao):
    service.ban_user(admin, regular_user.id_user)

    assert dao.users[regular_user.id_user].token is None


def test_ban_user_does_not_touch_other_users(service, admin, regular_user, dao):
    other = dao.add(_make_user(3, token="other_tok"))

    service.ban_user(admin, regular_user.id_user)

    assert dao.users[other.id_user].is_banned is False
    assert dao.users[other.id_user].token == "other_tok"


def test_ban_user_requires_admin(service, regular_user, dao):
    other = dao.add(_make_user(3))

    with pytest.raises(PermissionError):
        service.ban_user(regular_user, other.id_user)

    assert dao.users[other.id_user].is_banned is False


def test_ban_user_requires_a_caller(service, regular_user):
    with pytest.raises(PermissionError):
        service.ban_user(None, regular_user.id_user)


def test_ban_user_cannot_ban_himself(service, admin, dao):
    with pytest.raises(ValueError):
        service.ban_user(admin, admin.id_user)

    assert dao.users[admin.id_user].is_banned is False


def test_ban_user_unknown_user(service, admin):
    with pytest.raises(ValueError):
        service.ban_user(admin, 999999)


def test_ban_user_cannot_ban_another_admin(service, admin, dao):
    other_admin = dao.add(_make_user(3, role_user="admin"))

    with pytest.raises(ValueError):
        service.ban_user(admin, other_admin.id_user)

    assert dao.users[other_admin.id_user].is_banned is False


def test_ban_user_dao_failure(service, admin, regular_user, dao):
    dao.fail_update = True

    assert service.ban_user(admin, regular_user.id_user) is False
    assert dao.users[regular_user.id_user].is_banned is False


# ------------------------------------------------------------ run_data_import

def test_run_data_import_ok(service, admin, fake_run):
    result = service.run_data_import(admin)

    assert result["success"] is True
    assert result["returncode"] == 0
    assert result["stdout"] == "import ok"
    assert result["stderr"] == ""


def test_run_data_import_command(service, admin, fake_run):
    service.run_data_import(admin, timeout=42)

    args, kwargs = fake_run.call_args
    assert args[0] == [sys.executable, "-m", "utils.import_all_data"]
    assert kwargs["cwd"] == admin_service.SRC_DIR
    assert kwargs["timeout"] == 42
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True


def test_run_data_import_failure(service, admin, fake_run):
    fake_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="boom")

    result = service.run_data_import(admin)

    assert result["success"] is False
    assert result["returncode"] == 1
    assert result["stderr"] == "boom"


def test_run_data_import_timeout(service, admin, fake_run):
    fake_run.side_effect = subprocess.TimeoutExpired(cmd="import", timeout=5)

    result = service.run_data_import(admin, timeout=5)

    assert result["success"] is False
    assert result["returncode"] is None
    assert "Timeout" in result["stderr"]


def test_run_data_import_truncates_output(service, admin, fake_run):
    limit = admin_service.OUTPUT_TAIL_CHARS
    fake_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="a" * limit + "FIN", stderr="")

    result = service.run_data_import(admin)

    assert len(result["stdout"]) == limit
    assert result["stdout"].endswith("FIN")


def test_run_data_import_requires_admin(service, regular_user, fake_run):
    with pytest.raises(PermissionError):
        service.run_data_import(regular_user)

    fake_run.assert_not_called()


def test_run_data_import_requires_a_caller(service, fake_run):
    with pytest.raises(PermissionError):
        service.run_data_import(None)

    fake_run.assert_not_called()


# ---------------------------------------------------------- import : verrou

def test_run_data_import_refuses_concurrent_run(service, admin, fake_run):
    AdminService._import_lock.acquire()  # simule un import déjà en cours

    with pytest.raises(RuntimeError):
        service.run_data_import(admin)

    fake_run.assert_not_called()


def test_import_lock_released_after_success(service, admin, fake_run):
    service.run_data_import(admin)

    assert not AdminService._import_lock.locked()


def test_import_lock_released_after_failure(service, admin, fake_run):
    fake_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="boom")

    service.run_data_import(admin)

    assert not AdminService._import_lock.locked()


def test_import_lock_released_after_timeout(service, admin, fake_run):
    fake_run.side_effect = subprocess.TimeoutExpired(cmd="import", timeout=5)

    service.run_data_import(admin)

    assert not AdminService._import_lock.locked()


def test_import_lock_released_after_unexpected_error(service, admin, fake_run):
    fake_run.side_effect = OSError("python introuvable")

    with pytest.raises(OSError):
        service.run_data_import(admin)

    assert not AdminService._import_lock.locked()


def test_import_can_run_again_after_a_previous_run(service, admin, fake_run):
    service.run_data_import(admin)
    result = service.run_data_import(admin)

    assert result["success"] is True
    assert fake_run.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])