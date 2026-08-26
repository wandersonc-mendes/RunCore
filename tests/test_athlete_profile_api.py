import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from api.routers import profiles as router  # noqa: E402


class AthleteProfileApiTests(unittest.TestCase):
    def setUp(self):
        self.original_require_access = router.require_athlete_access
        self.original_details = router.details

        router.details = SimpleNamespace(
            get=lambda athlete_id: SimpleNamespace(
                personal={
                    "birth_date": "1990-08-25",
                    "weight": "72.4",
                    "height": "1.78",
                },
                parq={},
                training={},
            ),
        )

    def tearDown(self):
        router.require_athlete_access = self.original_require_access
        router.details = self.original_details

    def test_coach_profile_includes_personal_body_measurements(self):
        athlete = SimpleNamespace(
            id=7,
            name="Ana",
            email="ana@example.com",
            phone="",
            goal="10 km",
        )
        router.require_athlete_access = lambda athlete_id, coach: athlete

        result = router.get_athlete_profile(
            7,
            coach=SimpleNamespace(id=10, role="coach"),
        )

        self.assertEqual(result["personal"]["birth_date"], "1990-08-25")
        self.assertEqual(result["personal"]["weight"], "72.4")
        self.assertEqual(result["personal"]["height"], "1.78")

    def test_access_is_checked_before_profile_data_is_loaded(self):
        calls = []
        router.require_athlete_access = lambda athlete_id, coach: (
            calls.append("access")
            or (_ for _ in ()).throw(
                HTTPException(status_code=403, detail="Acesso negado."),
            )
        )
        router.details = SimpleNamespace(
            get=lambda athlete_id: calls.append("details"),
        )

        with self.assertRaises(HTTPException) as raised:
            router.get_athlete_profile(
                8,
                coach=SimpleNamespace(id=10, role="coach"),
            )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(calls, ["access"])

    def test_profile_completion_requires_weight_and_height(self):
        personal = {
            "name": "Ana",
            "birth_date": "1990-08-25",
            "sex": "Feminino",
            "phone": "11999999999",
            "city": "São Paulo",
            "state": "SP",
        }
        parq = {f"q{index}": "Não" for index in range(1, 8)}
        training = {
            "days": ["Seg"],
            "modality": "Corrida",
            "goal": "10 km",
        }

        result = router.profile_completion(personal, parq, training)

        self.assertFalse(result["complete"])
        self.assertIn("Peso", result["missing_fields"])
        self.assertIn("Altura", result["missing_fields"])

    def test_body_measurements_accept_valid_decimal_values(self):
        router.validate_body_measurements({
            "weight": "72,4",
            "height": "1.78",
        })

    def test_body_measurements_reject_out_of_range_height(self):
        with self.assertRaises(HTTPException) as raised:
            router.validate_body_measurements({
                "weight": "72.4",
                "height": "3.10",
            })

        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("Altura", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
