from sqlalchemy import select

from database.database import SessionLocal
from models.training_session import TrainingSession
from models.training_step import TrainingStep


class ActivityAnalysisService:

    DISTANCE_TOLERANCE = 0.08
    DURATION_TOLERANCE = 0.10

    @staticmethod
    def _pace_seconds(value):
        parts = str(value or "").split(":")

        if len(parts) != 2:
            return None

        try:
            minutes = int(parts[0])
            seconds = int(parts[1])
        except (TypeError, ValueError):
            return None

        if minutes < 0 or seconds < 0 or seconds >= 60:
            return None

        return (minutes * 60) + seconds

    @staticmethod
    def _distance_km(step):
        value = float(step.distance or 0)

        if str(step.distance_unit or "").lower() == "m":
            value /= 1000

        return value

    @classmethod
    def _expanded_steps(cls, steps):
        expanded = []

        for step in steps:
            distance_km = cls._distance_km(step)

            if distance_km <= 0:
                continue

            repetitions = max(
                1,
                int(step.repetitions or 1),
            )

            for repetition in range(repetitions):
                expanded.append({
                    "step_id": step.id,
                    "order": step.order,
                    "type": step.type,
                    "repetition": repetition + 1,
                    "repetitions": repetitions,
                    "distance_km": round(
                        distance_km,
                        3,
                    ),
                    "pace_min": step.pace_min or "",
                    "pace_max": step.pace_max or "",
                })

        return expanded

    @staticmethod
    def _range_status(
        value,
        minimum,
        maximum,
    ):
        if (
            value is None
            or minimum is None
            or maximum is None
        ):
            return "unknown"

        low = min(minimum, maximum)
        high = max(minimum, maximum)

        if low <= value <= high:
            return "inside"

        if value < low:
            return "below"

        return "above"

    @staticmethod
    def _distance_status(
        executed,
        planned,
        tolerance,
    ):
        if not planned or planned <= 0:
            return "unknown"

        minimum = planned * (1 - tolerance)
        maximum = planned * (1 + tolerance)

        if minimum <= executed <= maximum:
            return "inside"

        if executed < minimum:
            return "below"

        return "above"

    @classmethod
    def analyse(cls, activity, laps=None):
        if (
            activity is None
            or activity.training_session_id is None
        ):
            return {
                "available": False,
                "reason": "activity_not_linked",
            }

        with SessionLocal() as session:
            training_session = session.get(
                TrainingSession,
                activity.training_session_id,
            )

            if training_session is None:
                return {
                    "available": False,
                    "reason": "training_session_not_found",
                }

            steps = session.scalars(
                select(TrainingStep)
                .where(
                    TrainingStep.session_id
                    == training_session.id,
                )
                .order_by(
                    TrainingStep.order,
                    TrainingStep.id,
                )
            ).all()

            expanded_steps = cls._expanded_steps(steps)

        planned_distance = round(
            sum(
                item["distance_km"]
                for item in expanded_steps
            ),
            3,
        )

        executed_distance = round(
            float(activity.distance or 0),
            3,
        )

        distance_difference = round(
            executed_distance - planned_distance,
            3,
        )

        distance_variance_percent = (
            round(
                (
                    distance_difference
                    / planned_distance
                )
                * 100,
                1,
            )
            if planned_distance > 0
            else None
        )

        distance_status = cls._distance_status(
            executed_distance,
            planned_distance,
            cls.DISTANCE_TOLERANCE,
        )

        planned_duration = int(
            training_session.planned_duration or 0
        )

        executed_duration = int(
            activity.moving_time or 0
        )

        duration_difference = (
            executed_duration - planned_duration
            if planned_duration > 0
            else None
        )

        duration_variance_percent = (
            round(
                (
                    duration_difference
                    / planned_duration
                )
                * 100,
                1,
            )
            if planned_duration > 0
            else None
        )

        duration_status = (
            cls._distance_status(
                executed_duration,
                planned_duration,
                cls.DURATION_TOLERANCE,
            )
            if planned_duration > 0
            else "unknown"
        )

        paced_ranges = []

        for item in expanded_steps:
            pace_values = [
                cls._pace_seconds(
                    item["pace_min"],
                ),
                cls._pace_seconds(
                    item["pace_max"],
                ),
            ]

            pace_values = [
                value
                for value in pace_values
                if value is not None
            ]

            if len(pace_values) == 2:
                paced_ranges.append(
                    (
                        min(pace_values),
                        max(pace_values),
                    )
                )

        unique_pace_ranges = sorted(
            set(paced_ranges)
        )

        executed_pace = (
            round(1000 / activity.average_speed)
            if activity.average_speed
            and activity.average_speed > 0
            else None
        )

        overall_pace = {
            "status": "unknown",
            "planned_min_seconds": None,
            "planned_max_seconds": None,
            "executed_seconds": executed_pace,
        }

        if len(unique_pace_ranges) == 1:
            planned_min, planned_max = (
                unique_pace_ranges[0]
            )

            overall_pace = {
                "status": cls._range_status(
                    executed_pace,
                    planned_min,
                    planned_max,
                ),
                "planned_min_seconds": planned_min,
                "planned_max_seconds": planned_max,
                "executed_seconds": executed_pace,
            }

        lap_rows = laps or []
        blocks = []
        aligned = (
            bool(expanded_steps)
            and len(lap_rows) >= len(expanded_steps)
        )

        if aligned:
            for index, expected in enumerate(
                expanded_steps
            ):
                lap = lap_rows[index]
                lap_distance = round(
                    float(
                        lap.get("distance") or 0
                    ),
                    3,
                )

                lap_speed = lap.get(
                    "average_speed"
                )

                lap_pace = (
                    round(1000 / lap_speed)
                    if lap_speed and lap_speed > 0
                    else None
                )

                pace_values = [
                    cls._pace_seconds(
                        expected["pace_min"],
                    ),
                    cls._pace_seconds(
                        expected["pace_max"],
                    ),
                ]

                pace_values = [
                    value
                    for value in pace_values
                    if value is not None
                ]

                pace_status = (
                    cls._range_status(
                        lap_pace,
                        min(pace_values),
                        max(pace_values),
                    )
                    if len(pace_values) == 2
                    else "unknown"
                )

                expected_distance = expected[
                    "distance_km"
                ]

                block_tolerance = max(
                    0.05,
                    expected_distance * 0.16,
                )

                distance_block_status = (
                    cls._range_status(
                        lap_distance,
                        expected_distance
                        - block_tolerance,
                        expected_distance
                        + block_tolerance,
                    )
                )

                blocks.append({
                    **expected,
                    "lap_number": index + 1,
                    "executed_distance_km": (
                        lap_distance
                    ),
                    "executed_pace_seconds": (
                        lap_pace
                    ),
                    "average_heartrate": (
                        lap.get(
                            "average_heartrate"
                        )
                    ),
                    "distance_status": (
                        distance_block_status
                    ),
                    "pace_status": pace_status,
                })

        cadence_raw = activity.average_cadence

        cadence_total = (
            round(float(cadence_raw) * 2, 1)
            if cadence_raw is not None
            and str(activity.sport_type or "").lower()
            in {
                "run",
                "virtualrun",
                "trailrun",
            }
            else cadence_raw
        )

        confidence = "high"

        if planned_distance <= 0:
            confidence = "low"
        elif not aligned:
            confidence = "medium"

        return {
            "available": True,
            "confidence": confidence,
            "training_session": {
                "id": training_session.id,
                "name": training_session.workout_name,
                "scheduled_date": (
                    training_session.scheduled_date
                ),
            },
            "distance": {
                "planned_km": planned_distance,
                "executed_km": executed_distance,
                "difference_km": distance_difference,
                "variance_percent": (
                    distance_variance_percent
                ),
                "tolerance_percent": int(
                    cls.DISTANCE_TOLERANCE * 100
                ),
                "status": distance_status,
            },
            "duration": {
                "planned_seconds": planned_duration,
                "executed_seconds": executed_duration,
                "difference_seconds": (
                    duration_difference
                ),
                "variance_percent": (
                    duration_variance_percent
                ),
                "status": duration_status,
            },
            "pace": overall_pace,
            "heart_rate": {
                "average": activity.average_heartrate,
                "maximum": activity.max_heartrate,
            },
            "cadence": {
                "provider_raw": cadence_raw,
                "steps_per_minute": cadence_total,
            },
            "elevation_gain": (
                activity.total_elevation_gain
            ),
            "blocks": {
                "aligned": aligned,
                "expected_count": len(
                    expanded_steps
                ),
                "available_laps": len(lap_rows),
                "items": blocks,
            },
        }
