import sys
import unittest
from datetime import date
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from services.athlete_analytics_service import (  # noqa: E402
    AthleteAnalyticsService,
)


def activity(
    *,
    start_at,
    distance=10.0,
    moving_time=3000,
    elapsed_time=3060,
    heart_rate=150.0,
    cadence=176.0,
    sport_type="Run",
):
    return SimpleNamespace(
        start_at=start_at,
        distance=distance,
        moving_time=moving_time,
        elapsed_time=elapsed_time,
        average_heartrate=heart_rate,
        average_cadence=cadence,
        sport_type=sport_type,
    )


class AthleteAnalyticsServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AthleteAnalyticsService()

    def test_build_for_athlete_uses_repository_history(self):
        class FakeActivityRepository:
            def __init__(self):
                self.requested_athlete_id = None

            def list_for_athlete(self, athlete_id):
                self.requested_athlete_id = athlete_id

                return [
                    activity(
                        start_at=datetime(2026, 8, 1, 7, 0),
                        distance=10.0,
                        moving_time=3000,
                        elapsed_time=3060,
                        heart_rate=150,
                        cadence=176,
                    ),
                    activity(
                        start_at=datetime(2026, 8, 3, 7, 0),
                        distance=8.0,
                        moving_time=2400,
                        elapsed_time=2460,
                        heart_rate=148,
                        cadence=174,
                    ),
                ]

        repository = FakeActivityRepository()

        service = AthleteAnalyticsService(
            activity_repository=repository,
        )

        profile = service.build_for_athlete(
            42,
            reference_date=date(2026, 8, 7),
        )

        self.assertEqual(
            repository.requested_athlete_id,
            42,
        )
        self.assertEqual(
            profile["athlete_id"],
            42,
        )
        self.assertEqual(
            profile["activity_count"],
            2,
        )
        total_weekly_distance = sum(
            week["distance_km"]
            for week in profile["weekly"]
        )

        self.assertEqual(
            total_weekly_distance,
            18.0,
        )

    def test_build_profile_filters_non_running_activities(self):
        profile = self.service.build_profile(
            [
                activity(
                    start_at=datetime(2026, 8, 1, 7, 0),
                    sport_type="Run",
                ),
                activity(
                    start_at=datetime(2026, 8, 2, 7, 0),
                    sport_type="Ride",
                ),
            ],
            reference_date=date(2026, 8, 7),
        )

        self.assertEqual(profile["activity_count"], 1)
        self.assertEqual(len(profile["weekly"]), 1)

    def test_weekly_evolution_sums_volume_and_duration(self):
        result = self.service.weekly_evolution(
            [
                activity(
                    start_at=datetime(2026, 8, 3, 7, 0),
                    distance=8.0,
                    moving_time=2400,
                    elapsed_time=2460,
                ),
                activity(
                    start_at=datetime(2026, 8, 5, 7, 0),
                    distance=12.0,
                    moving_time=3600,
                    elapsed_time=3660,
                ),
            ]
        )

        self.assertEqual(
            result,
            [
                {
                    "week_start": "2026-08-03",
                    "activity_count": 2,
                    "distance_km": 20.0,
                    "moving_time_seconds": 6000,
                    "elapsed_time_seconds": 6120,
                }
            ],
        )

    def test_pace_baseline_requires_three_samples(self):
        samples = [
            activity(
                start_at=datetime(2026, 7, day, 7, 0),
                distance=10.0,
                moving_time=3000,
                heart_rate=148 + day,
                cadence=174 + day,
            )
            for day in (1, 2, 3)
        ]

        baselines = self.service.pace_baselines(samples)

        self.assertEqual(len(baselines), 1)

        baseline = baselines[0]

        self.assertEqual(baseline["key"], "300_330")
        self.assertEqual(baseline["label"], "5:00-5:30/km")
        self.assertEqual(baseline["activity_count"], 3)
        self.assertTrue(baseline["baseline_available"])
        self.assertEqual(baseline["total_distance_km"], 30.0)
        self.assertEqual(baseline["average_pace"], "5:00")
        self.assertEqual(baseline["heart_rate_sample_count"], 3)
        self.assertEqual(baseline["cadence_sample_count"], 3)

    def test_pace_baseline_uses_time_weighted_sensor_averages(self):
        samples = [
            activity(
                start_at=datetime(2026, 7, 1, 7, 0),
                distance=5.0,
                moving_time=1500,
                heart_rate=140,
                cadence=170,
            ),
            activity(
                start_at=datetime(2026, 7, 2, 7, 0),
                distance=10.0,
                moving_time=3000,
                heart_rate=160,
                cadence=180,
            ),
            activity(
                start_at=datetime(2026, 7, 3, 7, 0),
                distance=10.0,
                moving_time=3000,
                heart_rate=160,
                cadence=180,
            ),
        ]

        baseline = self.service.pace_baselines(samples)[0]

        self.assertEqual(baseline["average_heartrate"], 156.0)
        self.assertEqual(baseline["average_cadence"], 178.0)

    def test_compare_28_day_periods_calculates_objective_deltas(self):
        samples = [
            activity(
                start_at=datetime(2026, 8, 1, 7, 0),
                distance=10.0,
                moving_time=3000,
            ),
            activity(
                start_at=datetime(2026, 7, 10, 7, 0),
                distance=8.0,
                moving_time=2640,
            ),
        ]

        comparison = self.service.compare_28_day_periods(
            samples,
            reference_date=date(2026, 8, 7),
        )

        self.assertEqual(
            comparison["current"]["activity_count"],
            1,
        )
        self.assertEqual(
            comparison["current"]["distance_km"],
            10.0,
        )
        self.assertEqual(
            comparison["previous"]["activity_count"],
            1,
        )
        self.assertEqual(
            comparison["previous"]["distance_km"],
            8.0,
        )

        distance_delta = comparison["delta"]["distance_km"]

        self.assertEqual(distance_delta["absolute"], 2.0)
        self.assertEqual(distance_delta["percent"], 25.0)

    def test_data_quality_reports_missing_sensor_data(self):
        quality = self.service.data_quality(
            [
                activity(
                    start_at=datetime(2026, 8, 1, 7, 0),
                    heart_rate=150,
                    cadence=176,
                ),
                activity(
                    start_at=datetime(2026, 8, 2, 7, 0),
                    heart_rate=None,
                    cadence=None,
                ),
            ]
        )

        self.assertEqual(quality["activity_count"], 2)
        self.assertEqual(
            quality["fields"]["distance"]["coverage_percent"],
            100.0,
        )
        self.assertEqual(
            quality["fields"]["pace"]["coverage_percent"],
            100.0,
        )
        self.assertEqual(
            quality["fields"]["heart_rate"]["coverage_percent"],
            50.0,
        )
        self.assertEqual(
            quality["fields"]["cadence"]["coverage_percent"],
            50.0,
        )

    def test_analysis_availability_exposes_missing_capabilities(self):
        availability = self.service.analysis_availability(
            [
                activity(
                    start_at=datetime(2026, 8, 1, 7, 0),
                    heart_rate=None,
                    cadence=None,
                ),
            ],
            reference_date=date(2026, 8, 7),
        )

        self.assertTrue(
            availability["weekly_volume"]["available"]
        )
        self.assertFalse(
            availability["pace_baselines"]["available"]
        )
        self.assertEqual(
            availability["pace_baselines"]["reason"],
            "insufficient_samples_per_pace_band",
        )
        self.assertFalse(
            availability["heart_rate_by_pace"]["available"]
        )
        self.assertFalse(
            availability["cadence_by_pace"]["available"]
        )
        self.assertFalse(
            availability["comparison_28_days"]["available"]
        )
        self.assertEqual(
            availability["lap_or_stream_analysis"],
            {
                "available": False,
                "reason": "laps_and_streams_not_persisted",
            },
        )


if __name__ == "__main__":
    unittest.main()
