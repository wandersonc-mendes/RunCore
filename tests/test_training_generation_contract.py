import sys
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from core.training.training_cycle_builder import TrainingCycleBuilder
from core.training.training_zone import TrainingZone


class TrainingGenerationContractTest(unittest.TestCase):

    def test_initial_long_run_preserves_identity_and_easy_zone(self):
        cycle = TrainingCycleBuilder.initial(
            total_weeks=4,
            target_distance=10,
            training_days=[0, 2, 5],
        )

        long_run = cycle.weeks[0].days[5].workouts[0]

        self.assertEqual(long_run.name, "Longão")
        self.assertEqual(
            long_run.zone,
            TrainingZone.EASY.value,
        )
        self.assertEqual(long_run.estimated_rpe, 5)

    def test_initial_plan_keeps_exactly_three_training_days(self):
        cycle = TrainingCycleBuilder.initial(
            total_weeks=2,
            target_distance=10,
            training_days=[0, 2, 5],
        )

        for week in cycle.weeks:
            training_days = [
                day
                for day in week.days
                if day.workouts
            ]

            self.assertEqual(
                len(training_days),
                3,
            )

    def test_interval_session_uses_total_modeled_distance_in_km(self):
        cycle = TrainingCycleBuilder.base(
            vdot=52.2,
            total_weeks=4,
            target_distance=42,
        )

        sessions = TrainingCycleBuilder.to_training_sessions(
            training_id=999,
            cycle=cycle,
        )

        interval_session = next(
            session
            for session in sessions
            if int(session.repetitions or 0) > 0
        )

        week = cycle.weeks[
            interval_session.week - 1
        ]
        workout = week.days[
            interval_session.weekday
        ].workouts[0]

        expected_km = round(
            (
                (
                    float(workout.distance or 0)
                    + float(workout.recovery or 0)
                )
                * int(workout.repetitions or 0)
            )
            / 1000,
            3,
        )

        self.assertEqual(
            interval_session.planned_distance,
            expected_km,
        )

    def test_interval_session_preserves_step_distance_metadata(self):
        cycle = TrainingCycleBuilder.base(
            vdot=52.2,
            total_weeks=4,
            target_distance=42,
        )

        sessions = TrainingCycleBuilder.to_training_sessions(
            training_id=999,
            cycle=cycle,
        )

        interval_session = next(
            session
            for session in sessions
            if int(session.repetitions or 0) > 0
        )

        week = cycle.weeks[
            interval_session.week - 1
        ]
        workout = week.days[
            interval_session.weekday
        ].workouts[0]

        self.assertEqual(
            interval_session._generated_step_distance,
            float(workout.distance or 0),
        )


if __name__ == "__main__":
    unittest.main()
