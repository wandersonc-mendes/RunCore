import sys
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from core.training.training_cycle_builder import TrainingCycleBuilder


class TaperAndRaceWeekTest(unittest.TestCase):

    def test_final_weeks_reduce_volume_and_end_with_race(self):
        cycle = TrainingCycleBuilder.base(
            vdot=50,
            total_weeks=23,
            ipt_profile="Potente",
            target_distance=42.2,
        )

        week_21 = cycle.weeks[20]
        week_22 = cycle.weeks[21]
        week_23 = cycle.weeks[22]

        long_21 = week_21.days[6].workouts[0]
        long_22 = week_22.days[6].workouts[0]
        race = week_23.days[6].workouts[0]

        self.assertGreater(long_21.distance, long_22.distance)
        self.assertEqual(race.name, "Prova-alvo")
        self.assertEqual(race.distance, 42.2)

    def test_race_week_easy_run_is_reduced(self):
        cycle = TrainingCycleBuilder.base(
            vdot=50,
            total_weeks=23,
            target_distance=42.2,
        )

        easy_22 = cycle.weeks[21].days[0].workouts[0]
        easy_23 = cycle.weeks[22].days[0].workouts[0]

        self.assertLess(easy_23.distance, easy_22.distance)


if __name__ == "__main__":
    unittest.main()
