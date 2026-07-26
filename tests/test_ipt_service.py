import sys
import unittest
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

from core.physiology.ipt_service import IptService


class IptServiceTest(unittest.TestCase):

    def test_distance_protocol_calculation(self):

        result = IptService.calculate(
            protocol_type="distance",
            short_value=500,
            long_value=1600,
            short_result=102,
            long_result=370,
        )

        self.assertEqual(result.short_speed, 17.65)
        self.assertEqual(result.long_speed, 15.57)
        self.assertEqual(result.ipt_percentage, 11.78)
        self.assertEqual(result.profile, "Potente")

    def test_time_protocol_calculation(self):

        result = IptService.calculate(
            protocol_type="time",
            short_value=120,
            long_value=300,
            short_result=570,
            long_result=1320,
        )

        self.assertEqual(result.short_speed, 17.1)
        self.assertEqual(result.long_speed, 15.84)
        self.assertEqual(result.ipt_percentage, 7.37)
        self.assertEqual(result.profile, "Resistente")

    def test_classification_boundaries(self):

        self.assertEqual(
            IptService.classify(8.99)[0],
            "Resistente",
        )
        self.assertEqual(
            IptService.classify(9)[0],
            "Equilibrado",
        )
        self.assertEqual(
            IptService.classify(11)[0],
            "Equilibrado",
        )
        self.assertEqual(
            IptService.classify(11.01)[0],
            "Potente",
        )

    def test_rejects_invalid_protocol_type(self):

        with self.assertRaisesRegex(
            ValueError,
            "Tipo de protocolo IPT inv\u00e1lido",
        ):
            IptService.calculate(
                protocol_type="invalid",
                short_value=500,
                long_value=1600,
                short_result=100,
                long_result=360,
            )

    def test_rejects_zero_or_negative_values(self):

        with self.assertRaisesRegex(
            ValueError,
            "maiores que zero",
        ):
            IptService.calculate(
                protocol_type="distance",
                short_value=500,
                long_value=1600,
                short_result=0,
                long_result=360,
            )


if __name__ == "__main__":
    unittest.main()