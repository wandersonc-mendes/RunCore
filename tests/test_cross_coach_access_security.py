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


from api import access_control  # noqa: E402
from api.routers import evaluations  # noqa: E402
from api.routers import profiles  # noqa: E402


class FakeAthletes:
    def __init__(self):
        self.items = {
            1: SimpleNamespace(
                id=1,
                coach_user_id=10,
                name="Ana",
                email="ana@example.com",
                phone="",
                goal="",
            ),
            2: SimpleNamespace(
                id=2,
                coach_user_id=20,
                name="Bruno",
                email="bruno@example.com",
                phone="",
                goal="",
            ),
        }

    def get_by_id(self, athlete_id):
        return self.items.get(athlete_id)


class FakeAccess:
    def coach_has_athlete(self, coach_id, athlete_id):
        return False


class FakeEvaluationRepository:
    def __init__(self):
        self.deleted = []
        self.listed = []
        self.items = {
            100: SimpleNamespace(
                id=100,
                athlete_id=2,
            ),
        }

    def list_by_athlete(self, athlete_id):
        self.listed.append(athlete_id)
        return []

    def get_by_id(self, evaluation_id):
        return self.items.get(evaluation_id)

    def delete(self, evaluation_id):
        self.deleted.append(evaluation_id)
        return True


class CrossCoachAccessSecurityTests(unittest.TestCase):
    def setUp(self):
        self.original_athletes = access_control.athletes
        self.original_access = access_control.access

        access_control.athletes = FakeAthletes()
        access_control.access = FakeAccess()

        self.coach = SimpleNamespace(
            id=10,
            role="coach",
        )
        self.master = SimpleNamespace(
            id=1,
            role="master",
        )

    def tearDown(self):
        access_control.athletes = self.original_athletes
        access_control.access = self.original_access

    def test_shared_guard_denies_other_coach(self):
        with self.assertRaises(HTTPException) as raised:
            access_control.require_athlete_access(
                2,
                self.coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )

    def test_shared_guard_allows_master(self):
        athlete = access_control.require_athlete_access(
            2,
            self.master,
        )
        self.assertEqual(athlete.id, 2)

    def test_evaluation_list_denies_cross_coach(self):
        fake_repo = FakeEvaluationRepository()

        with patch.object(
            evaluations,
            "repository",
            fake_repo,
        ):
            with self.assertRaises(HTTPException) as raised:
                evaluations.list_evaluations(
                    2,
                    coach=self.coach,
                )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )
        self.assertEqual(
            fake_repo.listed,
            [],
        )

    def test_evaluation_delete_denies_cross_coach(self):
        fake_repo = FakeEvaluationRepository()

        with patch.object(
            evaluations,
            "repository",
            fake_repo,
        ):
            with self.assertRaises(HTTPException) as raised:
                evaluations.delete_evaluation(
                    100,
                    coach=self.coach,
                )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )
        self.assertEqual(
            fake_repo.deleted,
            [],
        )

    def test_profile_denies_cross_coach(self):
        with self.assertRaises(HTTPException) as raised:
            profiles.get_athlete_profile(
                2,
                coach=self.coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )


if __name__ == "__main__":
    unittest.main()
