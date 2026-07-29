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
