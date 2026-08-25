import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api.routers import integrations as router  # noqa: E402


class StravaActivityStreamsTests(unittest.TestCase):
    def setUp(self):
        self.originals = {
            "require_athlete_access": router.require_athlete_access,
            "activities": router.activities,
            "repository": router.repository,
            "refresh_strava_token": router.refresh_strava_token,
            "strava_request": router.strava_request,
            "feedbacks": router.feedbacks,
            "analyse": router.ActivityAnalysisService.analyse,
        }

    def tearDown(self):
        for name, value in self.originals.items():
            if name == "analyse":
                router.ActivityAnalysisService.analyse = value
            else:
                setattr(router, name, value)

    def configure_activity(self):
        activity = SimpleNamespace(
            id=4,
            integration_id=8,
            provider_activity_id="123456",
            name="Corrida",
            sport_type="Run",
            distance=2100,
            moving_time=630,
            start_at=None,
            training_session_id=None,
            max_cadence=None,
        )
        integration = SimpleNamespace(
            id=8,
            active=True,
            access_token="local-test-token",
            external_user_id="98765",
        )
        router.activities = SimpleNamespace(
            list_for_athlete=lambda athlete_id: [activity],
        )
        router.repository = SimpleNamespace(
            get_by_id=lambda integration_id: integration,
        )
        router.refresh_strava_token = lambda item: item
        router.feedbacks = SimpleNamespace(
            get_for_activity=lambda activity_id: None,
        )
        router.ActivityAnalysisService.analyse = lambda *args: {}
        return activity

    def test_coach_details_returns_optional_streams_links_and_splits(self):
        self.configure_activity()
        router.require_athlete_access = lambda athlete_id, coach: object()
        requested_urls = []

        def request(url, token):
            requested_urls.append(url)
            if url.endswith("/laps"):
                return []
            if "/streams?" in url:
                return {
                    "time": {"data": [0, 300, 600, 630]},
                    "distance": {"data": [0, 1000, 2000, 2100]},
                    "latlng": {"data": [[-23.5, -46.6], [-23.51, -46.61]]},
                    "altitude": {"data": [700, 705, 710, 711]},
                    "velocity_smooth": {"data": [0, 3.3, 3.3, 3.3]},
                }
            return {"elapsed_time": 640}

        router.strava_request = request
        result = router.athlete_strava_activity_details(
            2,
            4,
            coach=SimpleNamespace(id=10, role="coach"),
        )

        self.assertEqual(
            result["strava_profile_url"],
            "https://www.strava.com/athletes/98765",
        )
        self.assertEqual(
            result["strava_activity_url"],
            "https://www.strava.com/activities/123456",
        )
        self.assertTrue(result["streams"]["available"]["latlng"])
        self.assertFalse(result["streams"]["available"]["heartrate"])
        self.assertFalse(result["streams"]["physiology_ready"])
        self.assertEqual(len(result["streams"]["splits"]), 3)
        self.assertTrue(all(url.startswith(router.STRAVA_API_BASE_URL) for url in requested_urls))
        self.assertIn("key_by_type=true", requested_urls[-1])

    def test_derives_pace_when_phone_stream_has_time_and_distance(self):
        result = router.serialize_activity_streams({
            "time": [0, 300, 600],
            "distance": [0, 1000, 2000],
        })
        self.assertTrue(result["available"]["velocity_smooth"])
        self.assertTrue(result["pace_is_derived"])
        self.assertAlmostEqual(result["points"][1]["velocity_smooth"], 10 / 3)

    def test_access_denial_happens_before_activity_or_token_lookup(self):
        calls = []
        router.require_athlete_access = lambda athlete_id, coach: (
            calls.append("access")
            or (_ for _ in ()).throw(
                HTTPException(status_code=403, detail="Acesso negado."),
            )
        )
        router.activities = SimpleNamespace(
            list_for_athlete=lambda athlete_id: calls.append("activities"),
        )

        with self.assertRaises(HTTPException) as raised:
            router.athlete_strava_activity_details(
                2,
                4,
                coach=SimpleNamespace(id=99, role="coach"),
            )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(calls, ["access"])

    def test_normalizes_legacy_list_stream_response(self):
        result = router.normalize_strava_streams([
            {"type": "time", "data": [0, 10]},
            {"type": "heartrate", "data": [120, 125]},
            {"type": "unknown", "data": [1, 2]},
        ])
        self.assertEqual(result["time"], [0, 10])
        self.assertEqual(result["heartrate"], [120, 125])
        self.assertNotIn("unknown", result)


if __name__ == "__main__":
    unittest.main()
