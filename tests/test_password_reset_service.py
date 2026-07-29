from datetime import datetime
from types import SimpleNamespace

from services.auth.password_reset_service import PasswordResetService


class FakeUsers:

    def __init__(self, user):
        self.user = user
        self.password_hash = None

    def get_by_email(self, email):
        if self.user and self.user.email == email:
            return self.user
        return None

    def update_password(self, user_id, password_hash):
        if not self.user or self.user.id != user_id:
            return None
        self.password_hash = password_hash
        return self.user


class FakeTokens:

    def __init__(self):
        self.created = None
        self.invalidated = []
        self.valid = None
        self.used = []

    def has_recent_request(self, user_id, since):
        return False

    def invalidate_for_user(self, user_id):
        self.invalidated.append(user_id)

    def create(self, **values):
        self.created = values

    def get_valid_by_hash(self, token_hash):
        return self.valid

    def mark_as_used(self, token_id):
        self.used.append(token_id)


class FakeEmail:

    def __init__(self):
        self.messages = []

    def send(self, **message):
        self.messages.append(message)


def make_service(user):
    service = PasswordResetService(
        email_service=FakeEmail(),
    )
    service.users = FakeUsers(user)
    service.tokens = FakeTokens()
    return service


def test_request_reset_sends_link_but_does_not_return_token():
    user = SimpleNamespace(
        id=7,
        name="Atleta",
        email="atleta@example.com",
    )
    service = make_service(user)

    result = service.request_reset(
        user.email,
    )

    assert result is None
    assert service.tokens.created["token_hash"]
    assert "reset_token=" in service.email.messages[0]["text"]
    assert (
        service.tokens.created["token_hash"]
        not in service.email.messages[0]["text"]
    )


def test_request_reset_for_unknown_email_has_no_side_effect():
    service = make_service(None)

    result = service.request_reset(
        "missing@example.com",
    )

    assert result is None
    assert service.tokens.created is None
    assert service.email.messages == []


def test_reset_token_is_marked_used_and_sends_notification():
    user = SimpleNamespace(
        id=9,
        name="Treinador",
        email="coach@example.com",
    )
    service = make_service(user)
    service.tokens.valid = SimpleNamespace(
        id=31,
        user_id=user.id,
        expires_at=datetime.now(),
    )

    changed = service.reset_password(
        token="valid-secret-token",
        new_password="uma-senha-segura",
    )

    assert changed is True
    assert service.tokens.used == [31]
    assert service.users.password_hash
    assert len(service.email.messages) == 1
