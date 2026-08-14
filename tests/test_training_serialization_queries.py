import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from api.routers import trainings

class TrainingSerializationQueryTest(unittest.TestCase):

    def test_evaluation_is_loaded_once_per_training(self):
        training = SimpleNamespace(
            id=77,
            athlete_id=10,
            name="Planejamento Principal",
            methodology="Observação inicial",
            objective="Melhorar condicionamento",
            target_distance=5.0,
            start_date=date(2026, 8, 3),
            target_date=date(2026, 8, 30),
            active=True,
        )

        sessions = [
            SimpleNamespace(
                id=1001, week=1, weekday=0,
                workout_name="Corrida Fácil", zone="Easy",
                planned_distance=3.0, repetitions=0, recovery=0,
                objective="", notes="", completed=False,
                scheduled_date=date(2026, 8, 3),
            ),
            SimpleNamespace(
                id=1002, week=1, weekday=2,
                workout_name="Corrida Fácil", zone="Easy",
                planned_distance=3.0, repetitions=0, recovery=0,
                objective="", notes="", completed=False,
                scheduled_date=date(2026, 8, 5),
            ),
            SimpleNamespace(
                id=1003, week=1, weekday=4,
                workout_name="Longão", zone="Marathon",
                planned_distance=5.0, repetitions=0, recovery=0,
                objective="", notes="", completed=False,
                scheduled_date=date(2026, 8, 7),
            ),
        ]

        with (
            patch.object(
                trainings.session_repository,
                "list_by_training",
                return_value=sessions,
            ),
            patch.object(
                trainings.step_repository,
                "list_by_sessions",
                return_value={},
            ),
            patch.object(
                trainings,
                "get_optional_evaluation",
                return_value=None,
            ) as evaluation_lookup,
        ):
            result = trainings.serialize_training(training)

        self.assertEqual(evaluation_lookup.call_count, 1)
        self.assertEqual(len(result["sessions"]), 3)
        self.assertTrue(
            all(
                session["zone"] == "Avaliação necessária"
                for session in result["sessions"]
            )
        )

if __name__ == "__main__":
    unittest.main()
