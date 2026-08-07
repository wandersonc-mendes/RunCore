import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from api.routers import athletes as athletes_router  # noqa: E402


class FakeAthleteRepository:
    def __init__(self, athlete):
        self.athlete = athlete
        self.requested_id = None

    def get_by_id(self, athlete_id):
        self.requested_id = athlete_id
        return self.athlete


class FakeAccessRepository:
    def __init__(self, allowed):
        self.allowed = allowed
        self.calls = []

    def coach_has_athlete(self, coach_id, athlete_id):
        self.calls.append(
            (coach_id, athlete_id)
        )
        return self.allowed


class FakeAnalyticsService:
    def __init__(self):
        self.requested_id = None

    def build_for_athlete(self, athlete_id):
        self.requested_id = athlete_id
        return {
            "athlete_id": athlete_id,
            "activity_count": 7,
        }


class AthleteAnalyticsApiTests(unittest.TestCase):
    def setUp(self):
        self.original_repository = athletes_router.repository
        self.original_access = athletes_router.access
        self.original_analytics = athletes_router.analytics

    def tearDown(self):
        athletes_router.repository = self.original_repository
        athletes_router.access = self.original_access
        athletes_router.analytics = self.original_analytics

    def configure(
        self,
        *,
        athlete_exists=True,
        allowed=True,
    ):
        athlete = (
            SimpleNamespace(id=42)
            if athlete_exists
            else None
        )

        repository = FakeAthleteRepository(
            athlete,
        )
        access = FakeAccessRepository(
            allowed,
        )
        analytics = FakeAnalyticsService()

        athletes_router.repository = repository
        athletes_router.access = access
        athletes_router.analytics = analytics

        return repository, access, analytics

    def test_returns_404_when_athlete_does_not_exist(self):
        self.configure(
            athlete_exists=False,
        )

        coach = SimpleNamespace(
            id=10,
            role="coach",
        )

        with self.assertRaises(HTTPException) as raised:
            athletes_router.get_athlete_analytics(
                999,
                coach=coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            404,
        )
        self.assertEqual(
            raised.exception.detail,
            "Atleta não encontrado",
        )

    def test_denies_unlinked_coach(self):
        _, access, analytics = self.configure(
            allowed=False,
        )

        coach = SimpleNamespace(
            id=10,
            role="coach",
        )

        with self.assertRaises(HTTPException) as raised:
            athletes_router.get_athlete_analytics(
                42,
                coach=coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )
        self.assertEqual(
            access.calls,
            [(10, 42)],
        )
        self.assertIsNone(
            analytics.requested_id,
        )

    def test_allows_linked_coach(self):
        repository, access, analytics = self.configure(
            allowed=True,
        )

        coach = SimpleNamespace(
            id=10,
            role="coach",
        )

        result = athletes_router.get_athlete_analytics(
            42,
            coach=coach,
        )

        self.assertEqual(
            repository.requested_id,
            42,
        )
        self.assertEqual(
            access.calls,
            [(10, 42)],
        )
        self.assertEqual(
            analytics.requested_id,
            42,
        )
        self.assertEqual(
            result,
            {
                "athlete_id": 42,
                "activity_count": 7,
            },
        )

    def test_master_bypasses_coach_link_check(self):
        _, access, analytics = self.configure(
            allowed=False,
        )

        master = SimpleNamespace(
            id=1,
            role="master",
        )

        result = athletes_router.get_athlete_analytics(
            42,
            coach=master,
        )

        self.assertEqual(
            access.calls,
            [],
        )
        self.assertEqual(
            analytics.requested_id,
            42,
        )
        self.assertEqual(
            result["athlete_id"],
            42,
        )


if __name__ == "__main__":
    unittest.main()
