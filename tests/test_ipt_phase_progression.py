import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from core.training.training_plan_service import TrainingPlanService


def workout(week, day):
    training_day = next(item for item in week.days if item.day == day)
    return training_day.workouts[0]


class IptPhaseProgressionTest(unittest.TestCase):

    def build(self, week_number, profile):
        return TrainingPlanService.generate_base_week(
            vdot=50,
            week_number=week_number,
            total_weeks=12,
            interval_reps=8,
            threshold_run=8,
            ipt_profile=profile,
        )

    def test_power_profile_changes_across_phases(self):
        base = workout(self.build(2, "Potente"), "Quarta")
        development = workout(self.build(6, "Potente"), "Quarta")
        specific = workout(self.build(10, "Potente"), "Quarta")
        taper = workout(self.build(12, "Potente"), "Quarta")

        self.assertEqual(base.name, "Intervalado moderado")
        self.assertEqual(development.name, "Intervalado longo")
        self.assertEqual(specific.name, "Resistência de velocidade")
        self.assertEqual(taper.name, "Ativação intervalada")
        self.assertGreater(development.distance, base.distance)
        self.assertLess(
            taper.repetitions * taper.distance,
            development.repetitions * development.distance,
        )

    def test_resistant_profile_changes_across_phases(self):
        base = workout(self.build(2, "Resistente"), "Quarta")
        development = workout(self.build(6, "Resistente"), "Quarta")
        specific = workout(self.build(10, "Resistente"), "Quarta")
        taper = workout(self.build(12, "Resistente"), "Quarta")

        self.assertEqual(base.name, "Velocidade e economia")
        self.assertEqual(development.name, "Intervalado curto")
        self.assertEqual(specific.name, "Intervalado específico")
        self.assertEqual(taper.name, "Ativação de velocidade")

    def test_threshold_changes_by_phase(self):
        base = workout(self.build(2, "Potente"), "Sexta")
        development = workout(self.build(6, "Potente"), "Sexta")
        specific = workout(self.build(10, "Potente"), "Sexta")
        taper = workout(self.build(12, "Potente"), "Sexta")

        self.assertEqual(base.name, "Limiar controlado")
        self.assertEqual(development.name, "Limiar sustentado")
        self.assertEqual(specific.name, "Limiar específico")
        self.assertEqual(taper.name, "Limiar reduzido")
        self.assertLess(taper.distance, development.distance)


if __name__ == "__main__":
    unittest.main()
