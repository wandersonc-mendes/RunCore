from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.dependencies import require_admin
from api.routers import admin as admin_router


def user(**overrides):
    values = {
        "id": 1,
        "name": "Administrador",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_require_admin_rejects_coach():
    with pytest.raises(HTTPException) as error:
        require_admin(user(role="coach"))

    assert error.value.status_code == 403


def test_master_has_administrative_and_coach_access():
    from api.dependencies import require_coach

    master = user(role="master")

    assert require_admin(master) is master
    assert require_coach(master) is master


def test_admin_cannot_remove_own_access(monkeypatch):
    current = user()
    monkeypatch.setattr(
        admin_router.user_repository,
        "get_by_id",
        lambda _: current,
    )

    payload = admin_router.ManagedUserUpdate(
        name=current.name,
        role="coach",
        is_active=True,
    )

    with pytest.raises(HTTPException) as error:
        admin_router.update_user(
            current.id,
            payload,
            current,
        )

    assert error.value.status_code == 409


def test_last_active_admin_cannot_be_deactivated(monkeypatch):
    current = user(id=1)
    target = user(id=2, email="second@example.com")

    monkeypatch.setattr(
        admin_router.user_repository,
        "get_by_id",
        lambda _: target,
    )
    monkeypatch.setattr(
        admin_router.user_repository,
        "count_active_by_role",
        lambda _: 1,
    )

    payload = admin_router.ManagedUserUpdate(
        name=target.name,
        role="admin",
        is_active=False,
    )

    with pytest.raises(HTTPException) as error:
        admin_router.update_user(
            target.id,
            payload,
            current,
        )

    assert error.value.status_code == 409


def test_master_access_cannot_be_changed(monkeypatch):
    current = user(role="master")
    monkeypatch.setattr(
        admin_router.user_repository,
        "get_by_id",
        lambda _: current,
    )

    payload = admin_router.ManagedUserUpdate(
        name=current.name,
        role="admin",
        is_active=True,
    )

    with pytest.raises(HTTPException) as error:
        admin_router.update_user(
            current.id,
            payload,
            current,
        )

    assert error.value.status_code == 409


@pytest.mark.parametrize("role", ["admin", "master"])
def test_admin_and_master_can_create_coach(monkeypatch, role):
    current = user(role=role)
    created = user(
        id=8,
        name="Novo Treinador",
        email="novo@example.com",
        role="coach",
    )
    captured = {}

    monkeypatch.setattr(
        admin_router.user_repository,
        "email_exists",
        lambda _: False,
    )

    def create_coach_with_profile(**values):
        captured.update(values)
        return created

    monkeypatch.setattr(
        admin_router.user_repository,
        "create_coach_with_profile",
        create_coach_with_profile,
    )

    payload = admin_router.CoachCreate(
        name=created.name,
        email=created.email,
        password="senha-temporaria",
        cref="012345-G/SP",
        city="São Paulo",
        curriculum="Treinador de corrida.",
    )

    result = admin_router.create_coach(
        payload,
        require_admin(current),
    )

    assert result is created
    assert captured["profile"]["cref"] == "012345-G/SP"
    assert captured["profile"]["city"] == "São Paulo"
    assert captured["profile"]["curriculum"] == "Treinador de corrida."
    assert captured["is_active"] is True


def test_only_master_can_delete_student(client):
    class FakeUser:
        id = 900
        role = "admin"

    from api.routers import admin as admin_router

    client.app.dependency_overrides[admin_router.require_admin] = lambda: FakeUser()

    response = client.delete("/api/admin/users/12/student")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Apenas o usuário Master pode remover alunos."
    )

    client.app.dependency_overrides.clear()

