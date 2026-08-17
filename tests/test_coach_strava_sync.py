import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from api.routers import integrations  # noqa: E402


class FakeIntegrationRepository:
    def __init__(self, integration):
        self.integration = integration
        self.calls = []

    def get(self, user_id, provider):
        self.calls.append((user_id, provider))
        return self.integration


class FakeActivityRepository:
    def __init__(self, imported=0):
        self.imported = imported
        self.calls = []

    def sync_strava_batch(
        self,
        integration_id,
        data,
        athlete_id=None,
    ):
        self.calls.append(
            (integration_id, data, athlete_id)
        )
        return self.imported


class CoachStravaSyncTests(unittest.TestCase):
    def setUp(self):
        self.coach = SimpleNamespace(id=10, role="coach")
        self.athlete = SimpleNamespace(id=42, user_id=84)
        self.integration = SimpleNamespace(
            id=7,
            active=True,
            access_token="token",
        )

    def test_route_requires_post(self):
        route = next(
            route
            for route in integrations.router.routes
            if getattr(route, "path", None)
            == "/integrations/athletes/{athlete_id}/strava/sync"
        )

        self.assertEqual(route.methods, {"POST"})

    def call_sync(
        self,
        *,
        athlete=None,
        integration=None,
        imported=1,
    ):
        athlete = self.athlete if athlete is None else athlete
        integration = (
            self.integration
            if integration is None
            else integration
        )
        repository = FakeIntegrationRepository(integration)
        activity_repository = FakeActivityRepository(imported)
        data = [{"id": 1}, {"id": 2}]

        with (
            patch.object(
                integrations,
                "require_athlete_access",
                return_value=athlete,
            ) as access_guard,
            patch.object(integrations, "repository", repository),
            patch.object(
                integrations,
                "activities",
                activity_repository,
            ),
            patch.object(
                integrations,
                "refresh_strava_token",
                return_value=integration,
            ),
            patch.object(
                integrations,
                "strava_request",
                return_value=data,
            ),
        ):
            result = integrations.sync_athlete_strava_activities(
                42,
                coach=self.coach,
            )

        return (
            result,
            access_guard,
            repository,
            activity_repository,
            data,
        )

    def test_syncs_linked_athlete_and_returns_counts(self):
        (
            result,
            access_guard,
            repository,
            activity_repository,
            data,
        ) = self.call_sync()

        access_guard.assert_called_once_with(42, self.coach)
        self.assertEqual(repository.calls, [(84, "strava")])
        self.assertEqual(
            activity_repository.calls,
            [(7, data, 42)],
        )
        self.assertEqual(
            result,
            {"imported": 1, "updated": 1},
        )

    def test_rejects_athlete_without_linked_user(self):
        athlete = SimpleNamespace(id=42, user_id=None)

        with patch.object(
            integrations,
            "require_athlete_access",
            return_value=athlete,
        ):
            with self.assertRaises(HTTPException) as raised:
                integrations.sync_athlete_strava_activities(
                    42,
                    coach=self.coach,
                )

        self.assertEqual(raised.exception.status_code, 404)

    def test_rejects_inactive_integration(self):
        integration = SimpleNamespace(
            id=7,
            active=False,
        )

        with self.assertRaises(HTTPException) as raised:
            self.call_sync(integration=integration)

        self.assertEqual(raised.exception.status_code, 409)

    def test_rejects_missing_integration(self):
        repository = FakeIntegrationRepository(None)

        with (
            patch.object(
                integrations,
                "require_athlete_access",
                return_value=self.athlete,
            ),
            patch.object(integrations, "repository", repository),
        ):
            with self.assertRaises(HTTPException) as raised:
                integrations.sync_athlete_strava_activities(
                    42,
                    coach=self.coach,
                )

        self.assertEqual(raised.exception.status_code, 404)

    def test_access_is_checked_before_integration_lookup(self):
        with (
            patch.object(
                integrations,
                "require_athlete_access",
                side_effect=HTTPException(
                    status_code=403,
                    detail="Sem acesso.",
                ),
            ),
            patch.object(
                integrations,
                "repository",
            ) as repository,
        ):
            with self.assertRaises(HTTPException) as raised:
                integrations.sync_athlete_strava_activities(
                    42,
                    coach=self.coach,
                )

        self.assertEqual(raised.exception.status_code, 403)
        repository.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
