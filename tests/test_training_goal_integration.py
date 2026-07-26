import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))

from api.routers.trainings import goal_training_data, weeks_between_dates


class TrainingGoalIntegrationTest(unittest.TestCase):
    def test_weeks_are_calculated_from_goal_date(self):
        self.assertEqual(weeks_between_dates(date(2026, 7, 26), date(2026, 12, 31)), 23)

    def test_minimum_cycle_is_four_weeks(self):
        self.assertEqual(weeks_between_dates(date(2026, 7, 26), date(2026, 8, 10)), 4)

    def test_goal_overrides_training_definition(self):
        goal = SimpleNamespace(name='Maratona de dezembro', distance=42.2, target_date=date(2026, 12, 31), priority='Principal')
        result = goal_training_data(goal, date(2026, 7, 26))
        self.assertEqual(result['objective'], 'Maratona de dezembro')
        self.assertEqual(result['target_distance'], 42.2)
        self.assertEqual(result['target_date'], date(2026, 12, 31))
        self.assertEqual(result['total_weeks'], 23)

    def test_invalid_goal_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'posterior ao início'):
            weeks_between_dates(date(2026, 8, 30), date(2026, 8, 30))


if __name__ == '__main__':
    unittest.main()
