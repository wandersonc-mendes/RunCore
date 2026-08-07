from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Iterable


class AthleteAnalyticsService:
    # Camada determinística de cálculos do perfil analítico do atleta.

    RUNNING_TYPES = {
        "run",
        "running",
        "trailrun",
        "trailrunning",
        "virtualrun",
    }

    PACE_BAND_SECONDS = 30
    MIN_BASELINE_SAMPLES = 3

    def build_profile(
        self,
        activities: Iterable,
        *,
        reference_date: date | None = None,
    ) -> dict:
        reference_date = reference_date or date.today()
        running = self._running_activities(activities)

        return {
            "reference_date": reference_date.isoformat(),
            "activity_count": len(running),
            "weekly": self.weekly_evolution(running),
            "pace_baselines": self.pace_baselines(running),
            "period_comparison": self.compare_28_day_periods(
                running,
                reference_date=reference_date,
            ),
            "data_quality": self.data_quality(running),
            "analysis_availability": self.analysis_availability(
                running,
                reference_date=reference_date,
            ),
        }

    def weekly_evolution(self, activities: Iterable) -> list[dict]:
        buckets = defaultdict(
            lambda: {
                "activity_count": 0,
                "distance_km": 0.0,
                "moving_time_seconds": 0,
                "elapsed_time_seconds": 0,
            }
        )

        for activity in activities:
            activity_date = self._activity_date(activity)
            if activity_date is None:
                continue

            week_start = activity_date - timedelta(
                days=activity_date.weekday(),
            )
            bucket = buckets[week_start]
            bucket["activity_count"] += 1
            bucket["distance_km"] += self._positive_float(
                getattr(activity, "distance", None),
            )
            bucket["moving_time_seconds"] += self._positive_int(
                getattr(activity, "moving_time", None),
            )
            bucket["elapsed_time_seconds"] += self._positive_int(
                getattr(activity, "elapsed_time", None),
            )

        return [
            {
                "week_start": week_start.isoformat(),
                "activity_count": buckets[week_start]["activity_count"],
                "distance_km": round(
                    buckets[week_start]["distance_km"],
                    3,
                ),
                "moving_time_seconds": buckets[week_start][
                    "moving_time_seconds"
                ],
                "elapsed_time_seconds": buckets[week_start][
                    "elapsed_time_seconds"
                ],
            }
            for week_start in sorted(buckets)
        ]

    def pace_baselines(self, activities: Iterable) -> list[dict]:
        groups = defaultdict(list)

        for activity in activities:
            pace = self._pace_seconds_per_km(activity)
            if pace is None:
                continue

            key, lower, upper = self._pace_band(pace)
            groups[key].append(
                {
                    "activity": activity,
                    "lower": lower,
                    "upper": upper,
                }
            )

        result = []

        for key in sorted(
            groups,
            key=lambda item: groups[item][0]["lower"],
        ):
            samples = groups[key]
            lower = samples[0]["lower"]
            upper = samples[0]["upper"]

            total_distance = sum(
                self._positive_float(
                    getattr(sample["activity"], "distance", None)
                )
                for sample in samples
            )
            total_time = sum(
                self._positive_int(
                    getattr(sample["activity"], "moving_time", None)
                )
                for sample in samples
            )
            aggregate_pace = (
                total_time / total_distance
                if total_time > 0 and total_distance > 0
                else None
            )
            heart_rate = self._time_weighted_average(
                samples,
                "average_heartrate",
            )
            cadence = self._time_weighted_average(
                samples,
                "average_cadence",
            )

            result.append(
                {
                    "key": key,
                    "label": (
                        f"{self._format_pace(lower)}-"
                        f"{self._format_pace(upper)}/km"
                    ),
                    "lower_seconds_per_km": lower,
                    "upper_seconds_per_km": upper,
                    "activity_count": len(samples),
                    "baseline_available": (
                        len(samples) >= self.MIN_BASELINE_SAMPLES
                    ),
                    "total_distance_km": round(total_distance, 3),
                    "total_moving_time_seconds": total_time,
                    "average_pace_seconds_per_km": (
                        round(aggregate_pace, 1)
                        if aggregate_pace is not None
                        else None
                    ),
                    "average_pace": (
                        self._format_pace(aggregate_pace)
                        if aggregate_pace is not None
                        else None
                    ),
                    "average_heartrate": heart_rate["average"],
                    "heart_rate_sample_count": heart_rate[
                        "sample_count"
                    ],
                    "average_cadence": cadence["average"],
                    "cadence_sample_count": cadence[
                        "sample_count"
                    ],
                }
            )

        return result

    def compare_28_day_periods(
        self,
        activities: Iterable,
        *,
        reference_date: date | None = None,
    ) -> dict:
        reference_date = reference_date or date.today()
        current_start = reference_date - timedelta(days=27)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=27)

        current_metrics = self._period_metrics(
            self._between(
                activities,
                current_start,
                reference_date,
            )
        )
        previous_metrics = self._period_metrics(
            self._between(
                activities,
                previous_start,
                previous_end,
            )
        )

        compared_fields = (
            "activity_count",
            "distance_km",
            "moving_time_seconds",
            "elapsed_time_seconds",
            "average_pace_seconds_per_km",
            "average_heartrate",
            "average_cadence",
        )

        return {
            "current": {
                "start": current_start.isoformat(),
                "end": reference_date.isoformat(),
                **current_metrics,
            },
            "previous": {
                "start": previous_start.isoformat(),
                "end": previous_end.isoformat(),
                **previous_metrics,
            },
            "delta": {
                field: self._delta(
                    current_metrics[field],
                    previous_metrics[field],
                )
                for field in compared_fields
            },
        }

    def data_quality(self, activities: Iterable) -> dict:
        activities = list(activities)
        total = len(activities)

        checks = {
            "date": lambda item: self._activity_date(item) is not None,
            "distance": lambda item: self._positive_float(
                getattr(item, "distance", None)
            ) > 0,
            "moving_time": lambda item: self._positive_int(
                getattr(item, "moving_time", None)
            ) > 0,
            "pace": lambda item: (
                self._pace_seconds_per_km(item) is not None
            ),
            "heart_rate": lambda item: self._is_positive_number(
                getattr(item, "average_heartrate", None)
            ),
            "cadence": lambda item: self._is_positive_number(
                getattr(item, "average_cadence", None)
            ),
        }

        fields = {}

        for name, check in checks.items():
            available = sum(
                1
                for activity in activities
                if check(activity)
            )
            fields[name] = {
                "available": available,
                "missing": max(total - available, 0),
                "coverage_percent": self._coverage(
                    available,
                    total,
                ),
            }

        overall = (
            round(
                sum(
                    item["coverage_percent"]
                    for item in fields.values()
                )
                / len(fields),
                1,
            )
            if total > 0
            else 0.0
        )

        return {
            "activity_count": total,
            "overall_coverage_percent": overall,
            "fields": fields,
        }

    def analysis_availability(
        self,
        activities: Iterable,
        *,
        reference_date: date | None = None,
    ) -> dict:
        reference_date = reference_date or date.today()
        activities = list(activities)

        with_pace = [
            activity
            for activity in activities
            if self._pace_seconds_per_km(activity) is not None
        ]
        with_hr = [
            activity
            for activity in with_pace
            if self._is_positive_number(
                getattr(activity, "average_heartrate", None)
            )
        ]
        with_cadence = [
            activity
            for activity in with_pace
            if self._is_positive_number(
                getattr(activity, "average_cadence", None)
            )
        ]

        current_start = reference_date - timedelta(days=27)
        previous_start = reference_date - timedelta(days=55)
        previous_end = current_start - timedelta(days=1)

        current_count = len(
            self._between(
                activities,
                current_start,
                reference_date,
            )
        )
        previous_count = len(
            self._between(
                activities,
                previous_start,
                previous_end,
            )
        )

        band_counts = defaultdict(int)
        for activity in with_pace:
            pace = self._pace_seconds_per_km(activity)
            if pace is not None:
                key, _, _ = self._pace_band(pace)
                band_counts[key] += 1

        available_bands = sum(
            1
            for count in band_counts.values()
            if count >= self.MIN_BASELINE_SAMPLES
        )

        return {
            "weekly_volume": self._availability(
                bool(activities),
                "no_running_activities",
            ),
            "weekly_duration": self._availability(
                bool(activities),
                "no_running_activities",
            ),
            "pace_baselines": {
                **self._availability(
                    available_bands > 0,
                    "insufficient_samples_per_pace_band",
                ),
                "minimum_samples_per_band": (
                    self.MIN_BASELINE_SAMPLES
                ),
                "available_band_count": available_bands,
            },
            "heart_rate_by_pace": {
                **self._availability(
                    bool(with_hr),
                    "missing_pace_or_heart_rate",
                ),
                "sample_count": len(with_hr),
            },
            "cadence_by_pace": {
                **self._availability(
                    bool(with_cadence),
                    "missing_pace_or_cadence",
                ),
                "sample_count": len(with_cadence),
            },
            "comparison_28_days": {
                **self._availability(
                    current_count > 0 and previous_count > 0,
                    "missing_activities_in_one_period",
                ),
                "current_period_activity_count": current_count,
                "previous_period_activity_count": previous_count,
            },
            "lap_or_stream_analysis": {
                "available": False,
                "reason": "laps_and_streams_not_persisted",
            },
        }

    def _running_activities(self, activities: Iterable) -> list:
        result = []

        for activity in activities:
            sport_type = str(
                getattr(activity, "sport_type", "") or ""
            )
            normalized = (
                sport_type
                .replace("_", "")
                .replace(" ", "")
                .lower()
            )

            if normalized not in self.RUNNING_TYPES:
                continue

            if self._activity_date(activity) is None:
                continue

            result.append(activity)

        result.sort(
            key=lambda item: self._activity_date(item) or date.min
        )
        return result

    def _period_metrics(self, activities: Iterable) -> dict:
        activities = list(activities)

        distance = sum(
            self._positive_float(
                getattr(activity, "distance", None)
            )
            for activity in activities
        )
        moving_time = sum(
            self._positive_int(
                getattr(activity, "moving_time", None)
            )
            for activity in activities
        )
        elapsed_time = sum(
            self._positive_int(
                getattr(activity, "elapsed_time", None)
            )
            for activity in activities
        )

        aggregate_pace = (
            moving_time / distance
            if moving_time > 0 and distance > 0
            else None
        )
        samples = [
            {"activity": activity}
            for activity in activities
        ]
        heart_rate = self._time_weighted_average(
            samples,
            "average_heartrate",
        )
        cadence = self._time_weighted_average(
            samples,
            "average_cadence",
        )

        return {
            "activity_count": len(activities),
            "distance_km": round(distance, 3),
            "moving_time_seconds": moving_time,
            "elapsed_time_seconds": elapsed_time,
            "average_pace_seconds_per_km": (
                round(aggregate_pace, 1)
                if aggregate_pace is not None
                else None
            ),
            "average_pace": (
                self._format_pace(aggregate_pace)
                if aggregate_pace is not None
                else None
            ),
            "average_heartrate": heart_rate["average"],
            "average_cadence": cadence["average"],
        }

    def _time_weighted_average(
        self,
        samples: Iterable[dict],
        field: str,
    ) -> dict:
        weighted_sum = 0.0
        total_weight = 0
        sample_count = 0

        for sample in samples:
            activity = sample["activity"]
            value = getattr(activity, field, None)

            if not self._is_positive_number(value):
                continue

            weight = self._positive_int(
                getattr(activity, "moving_time", None)
            )
            if weight <= 0:
                continue

            weighted_sum += float(value) * weight
            total_weight += weight
            sample_count += 1

        return {
            "average": (
                round(weighted_sum / total_weight, 1)
                if total_weight > 0
                else None
            ),
            "sample_count": sample_count,
        }

    def _pace_seconds_per_km(self, activity) -> float | None:
        distance = self._positive_float(
            getattr(activity, "distance", None)
        )
        moving_time = self._positive_int(
            getattr(activity, "moving_time", None)
        )

        if distance <= 0 or moving_time <= 0:
            return None

        return moving_time / distance

    def _pace_band(
        self,
        pace_seconds: float,
    ) -> tuple[str, int, int]:
        width = self.PACE_BAND_SECONDS
        lower = int(pace_seconds // width) * width
        upper = lower + width
        return f"{lower}_{upper}", lower, upper

    def _between(
        self,
        activities: Iterable,
        start: date,
        end: date,
    ) -> list:
        return [
            activity
            for activity in activities
            if (
                (activity_date := self._activity_date(activity))
                is not None
                and start <= activity_date <= end
            )
        ]

    def _activity_date(self, activity) -> date | None:
        value = getattr(activity, "start_at", None)

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None

    def _delta(self, current, previous) -> dict:
        if current is None or previous is None:
            return {
                "absolute": None,
                "percent": None,
            }

        current = float(current)
        previous = float(previous)

        return {
            "absolute": round(current - previous, 3),
            "percent": (
                round(
                    ((current - previous) / previous) * 100,
                    1,
                )
                if previous != 0
                else None
            ),
        }

    def _availability(
        self,
        available: bool,
        unavailable_reason: str,
    ) -> dict:
        return {
            "available": available,
            "reason": (
                None
                if available
                else unavailable_reason
            ),
        }

    def _coverage(self, available: int, total: int) -> float:
        if total <= 0:
            return 0.0

        return round(available / total * 100, 1)

    def _is_positive_number(self, value) -> bool:
        try:
            return value is not None and float(value) > 0
        except (TypeError, ValueError):
            return False

    def _positive_float(self, value) -> float:
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            return 0.0

        return number if number > 0 else 0.0

    def _positive_int(self, value) -> int:
        try:
            number = int(value or 0)
        except (TypeError, ValueError):
            return 0

        return number if number > 0 else 0

    def _format_pace(self, seconds_per_km: float) -> str:
        total_seconds = int(round(seconds_per_km))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
