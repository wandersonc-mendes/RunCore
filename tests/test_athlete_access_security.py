import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(
        0,
        str(SRC),
    )


from api.routers import athletes as router  # noqa: E402
from api.schemas import AthleteCreate  # noqa: E402


class FakeRepository:
    def __init__(self):
        self.items = {
            1: SimpleNamespace(
                id=1,
                name="Ana",
                coach_user_id=10,
            ),
            2: SimpleNamespace(
                id=2,
                name="Bruno",
                coach_user_id=20,
            ),
            3: SimpleNamespace(
                id=3,
                name="Carlos",
                coach_user_id=None,
            ),
        }
        self.created_kwargs = None
        self.updated_ids = []
        self.deleted_ids = []
        self.list_all_calls = 0

    def list_all(self):
        self.list_all_calls += 1
        return list(self.items.values())

    def list_by_coach(self, coach_id):
        return [
            item
            for item in self.items.values()
            if item.coach_user_id == coach_id
        ]

    def get_by_id(self, athlete_id):
        return self.items.get(athlete_id)

    def create(self, **kwargs):
        self.created_kwargs = kwargs
        athlete = SimpleNamespace(
            id=99,
            name=kwargs["name"],
            coach_user_id=kwargs.get(
                "coach_user_id",
            ),
            phone=kwargs.get("phone", ""),
            email=kwargs.get("email", ""),
            goal=kwargs.get("goal", ""),
            active=kwargs.get("active", True),
            notes=kwargs.get("notes", ""),
        )
        self.items[99] = athlete
        return athlete

    def update(self, athlete_id, **kwargs):
        self.updated_ids.append(athlete_id)
        return athlete_id in self.items

    def delete(self, athlete_id):
        self.deleted_ids.append(athlete_id)
        return athlete_id in self.items


class FakeAccess:
    def __init__(self):
        self.links = {
            (10, 3),
        }
        self.created_links = []

    def coach_has_athlete(
        self,
        coach_id,
        athlete_id,
    ):
        return (
            coach_id,
            athlete_id,
        ) in self.links

    def athletes_for_coach(
        self,
        coach_id,
    ):
        return [
            SimpleNamespace(
                id=3,
                name="Carlos",
                coach_user_id=None,
            )
        ] if coach_id == 10 else []

    def link_coach_to_athlete(
        self,
        coach_id,
        athlete_id,
    ):
        self.created_links.append(
            (
                coach_id,
                athlete_id,
            )
        )


class AthleteAccessSecurityTests(
    unittest.TestCase,
):
    def setUp(self):
        self.original_repository = (
            router.repository
        )
        self.original_access = router.access

        self.repository = FakeRepository()
        self.access = FakeAccess()

        router.repository = self.repository
        router.access = self.access

        self.coach = SimpleNamespace(
            id=10,
            role="coach",
        )
        self.master = SimpleNamespace(
            id=1,
            role="master",
        )

    def tearDown(self):
        router.repository = (
            self.original_repository
        )
        router.access = self.original_access

    def test_coach_list_is_scoped(self):
        result = router.list_athletes(
            coach=self.coach,
        )

        self.assertEqual(
            [item.id for item in result],
            [1, 3],
        )
        self.assertEqual(
            self.repository.list_all_calls,
            0,
        )

    def test_master_lists_all(self):
        result = router.list_athletes(
            coach=self.master,
        )

        self.assertEqual(
            {item.id for item in result},
            {1, 2, 3},
        )
        self.assertEqual(
            self.repository.list_all_calls,
            1,
        )

    def test_get_rejects_other_coach_athlete(self):
        with self.assertRaises(
            HTTPException
        ) as raised:
            router.get_athlete(
                2,
                coach=self.coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )

    def test_update_rejects_other_coach_athlete(self):
        payload = SimpleNamespace(
            name="Bruno",
            phone="",
            email="",
            goal="",
            active=True,
            notes="",
        )

        with self.assertRaises(
            HTTPException
        ) as raised:
            router.update_athlete(
                2,
                payload,
                coach=self.coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )
        self.assertEqual(
            self.repository.updated_ids,
            [],
        )

    def test_delete_rejects_other_coach_athlete(self):
        with self.assertRaises(
            HTTPException
        ) as raised:
            router.delete_athlete(
                2,
                coach=self.coach,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )
        self.assertEqual(
            self.repository.deleted_ids,
            [],
        )

    def test_create_assigns_and_links_coach(self):
        payload = AthleteCreate(
            name="Daniel",
            phone="",
            email="daniel@example.com",
            goal="5 km",
            active=True,
            notes="",
        )

        result = router.create_athlete(
            payload,
            coach=self.coach,
        )

        self.assertEqual(
            result.coach_user_id,
            10,
        )
        self.assertEqual(
            self.repository.created_kwargs[
                "coach_user_id"
            ],
            10,
        )
        self.assertEqual(
            self.access.created_links,
            [(10, 99)],
        )

    def test_legacy_link_still_allows_access(self):
        result = router.get_athlete(
            3,
            coach=self.coach,
        )

        self.assertEqual(
            result.id,
            3,
        )


if __name__ == "__main__":
    unittest.main()
