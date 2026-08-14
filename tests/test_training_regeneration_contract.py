import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from core.training.training_persistence_service import (
    TrainingPersistenceService,
)


class FakeSessionRepository:

    def __init__(self, existing=None):
        self.existing = list(existing or [])
        self.created = []
        self.deleted = []

    def list_by_training(self, training_id):
        return list(self.existing)

    def create_many(self, sessions):
        self.created = list(sessions)

        for index, session in enumerate(
            self.created,
            start=1,
        ):
            session.id = 1000 + index

    def delete_regenerable_by_training(
        self,
        training_id,
        today,
    ):
        self.deleted.append(
            (training_id, today)
        )


class FakeStepService:

    def __init__(self):
        self.saved = []

    def save(self, session_id, steps):
        self.saved.append(
            (session_id, steps)
        )


class FakeTrainingRepository:

    def __init__(self, training):
        self.training = training
        self.updated = []

    def get_by_id(self, training_id):
        return self.training

    def update(self, training):
        self.updated.append(training)
        return training


class FixedDate(date):

    @classmethod
    def today(cls):
        return cls(2026, 8, 13)


class TrainingRegenerationContractTest(unittest.TestCase):

    def make_service(self):
        service = object.__new__(
            TrainingPersistenceService
        )
        service.session_repository = (
            FakeSessionRepository()
        )
        service.step_service = FakeStepService()
        service.training_repository = (
            FakeTrainingRepository(None)
        )
        return service

    def test_generation_uses_civil_week_and_skips_days_before_start(self):
        service = self.make_service()

        service._generate_sessions(
            training_id=77,
            vdot=None,
            total_weeks=2,
            target_distance=10,
            training_days=[0, 2, 4],
            start_date=date(2026, 8, 12),
        )

        generated_dates = [
            session.scheduled_date
            for session
            in service.session_repository.created
        ]

        self.assertEqual(
            generated_dates,
            [
                date(2026, 8, 12),
                date(2026, 8, 14),
                date(2026, 8, 17),
                date(2026, 8, 19),
                date(2026, 8, 21),
            ],
        )

        self.assertEqual(
            len(service.step_service.saved),
            5,
        )

    def test_generation_respects_excluded_dates(self):
        service = self.make_service()

        service._generate_sessions(
            training_id=77,
            vdot=None,
            total_weeks=2,
            target_distance=10,
            training_days=[0, 2, 4],
            start_date=date(2026, 8, 12),
            excluded_dates={
                date(2026, 8, 19),
            },
        )

        generated_dates = {
            session.scheduled_date
            for session
            in service.session_repository.created
        }

        self.assertNotIn(
            date(2026, 8, 19),
            generated_dates,
        )

        self.assertEqual(
            len(service.session_repository.created),
            4,
        )

        self.assertEqual(
            len(service.step_service.saved),
            4,
        )

    def test_regeneration_preserves_manual_completed_and_past_dates(self):
        sessions = [
            SimpleNamespace(
                week=1,
                scheduled_date=date(2026, 8, 12),
                manual_override=False,
                completed=False,
            ),
            SimpleNamespace(
                week=1,
                scheduled_date=date(2026, 8, 14),
                manual_override=True,
                completed=False,
            ),
            SimpleNamespace(
                week=1,
                scheduled_date=date(2026, 8, 15),
                manual_override=False,
                completed=True,
            ),
            SimpleNamespace(
                week=1,
                scheduled_date=date(2026, 8, 16),
                manual_override=False,
                completed=False,
            ),
        ]

        training = SimpleNamespace(
            id=77,
            start_date=date(2026, 8, 3),
            target_distance=42,
        )

        service = object.__new__(
            TrainingPersistenceService
        )
        service.session_repository = (
            FakeSessionRepository(sessions)
        )
        service.training_repository = (
            FakeTrainingRepository(training)
        )
        service.step_service = FakeStepService()

        captured = {}

        def fake_generate_sessions(
            training_id,
            vdot,
            total_weeks,
            ipt_profile=None,
            target_distance=None,
            training_days=None,
            start_date=None,
            excluded_dates=None,
        ):
            captured["training_id"] = training_id
            captured["excluded_dates"] = (
                set(excluded_dates or set())
            )
            captured["start_date"] = start_date

        service._generate_sessions = (
            fake_generate_sessions
        )

        with patch(
            "core.training.training_persistence_service.date",
            FixedDate,
        ):
            service.regenerate_training(
                training_id=77,
                vdot=52.2,
                total_weeks=4,
            )

        self.assertEqual(
            captured["excluded_dates"],
            {
                date(2026, 8, 12),
                date(2026, 8, 14),
                date(2026, 8, 15),
            },
        )

        self.assertNotIn(
            date(2026, 8, 16),
            captured["excluded_dates"],
        )

        self.assertEqual(
            service.session_repository.deleted,
            [
                (
                    77,
                    date(2026, 8, 13),
                )
            ],
        )

        self.assertEqual(
            captured["start_date"],
            date(2026, 8, 3),
        )


if __name__ == "__main__":
    unittest.main()
