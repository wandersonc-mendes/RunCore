import sys
import unittest
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

from core.training.training_plan_service import TrainingPlanService


def workout_for(week, day_name):
    day = next(item for item in week.days if item.day == day_name)
    return day.workouts[0]


class IptTrainingIntegrationTest(unittest.TestCase):

    def test_without_ipt_keeps_default_structure(self):
        week = TrainingPlanService.generate_base_week(
            vdot=50,
            interval_reps=8,
            total_weeks=8,
        )

        interval = workout_for(week, "Quarta")
        threshold = workout_for(week, "Sexta")

        self.assertEqual(interval.name, "Intervalado")
        self.assertEqual(interval.repetitions, 8)
        self.assertEqual(interval.distance, 400)
        self.assertEqual(interval.recovery, 200)
        self.assertEqual(threshold.name, "Limiar")

    def test_resistant_profile_preserves_work_volume_in_base_phase(self):
        week = TrainingPlanService.generate_base_week(
            vdot=50,
            week_number=1,
            total_weeks=8,
            interval_reps=8,
            ipt_profile="Resistente",
        )

        interval = workout_for(week, "Quarta")
        threshold = workout_for(week, "Sexta")

        self.assertEqual(interval.name, "Velocidade e economia")
        self.assertEqual(interval.repetitions, 16)
        self.assertEqual(interval.distance, 200)
        self.assertEqual(interval.recovery, 100)
        self.assertEqual(interval.repetitions * interval.distance, 3200)
        self.assertEqual(threshold.name, "Limiar controlado")

    def test_balanced_profile_keeps_default_structure(self):
        week = TrainingPlanService.generate_base_week(
            vdot=50,
            interval_reps=8,
            total_weeks=8,
            ipt_profile="Equilibrado",
        )

        interval = workout_for(week, "Quarta")

        self.assertEqual(interval.name, "Intervalado")
        self.assertEqual(interval.repetitions, 8)
        self.assertEqual(interval.distance, 400)
        self.assertEqual(interval.repetitions * interval.distance, 3200)

    def test_power_profile_preserves_work_volume_in_base_phase(self):
        week = TrainingPlanService.generate_base_week(
            vdot=50,
            week_number=1,
            total_weeks=8,
            interval_reps=8,
            ipt_profile="Potente",
        )

        interval = workout_for(week, "Quarta")
        threshold = workout_for(week, "Sexta")

        self.assertEqual(interval.name, "Intervalado moderado")
        self.assertEqual(interval.repetitions, 8)
        self.assertEqual(interval.distance, 400)
        self.assertEqual(interval.recovery, 200)
        self.assertEqual(interval.repetitions * interval.distance, 3200)
        self.assertEqual(threshold.name, "Limiar controlado")


if __name__ == "__main__":
    unittest.main()
