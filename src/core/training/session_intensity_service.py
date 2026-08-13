from __future__ import annotations

from core.physiology.heart_rate_service import (
    HeartRateService,
)
from core.physiology.pace_service import PaceService


INTENSITY_LABELS = {
    1: "Regenerativo / leve",
    2: "Rodagem aeróbia",
    3: "Moderado / ritmo sustentado",
    4: "Limiar / forte",
    5: "VO₂ / tiros mais intensos",
}

NON_PRIMARY_TYPES = {
    "aquecimento",
    "desaquecimento",
    "recuperação",
    "recuperacao",
    "descanso",
}


def _pace_seconds(value):
    if not value:
        return None

    raw = str(value).strip()

    if ":" not in raw:
        return None

    try:
        minutes, seconds = raw.split(":", 1)
        return int(minutes) * 60 + int(seconds)
    except (TypeError, ValueError):
        return None


def _average(values):
    valid = [
        float(value)
        for value in values
        if value is not None
    ]

    if not valid:
        return None

    return sum(valid) / len(valid)


class SessionIntensityService:

    @staticmethod
    def _pace_zone(step, vdot):
        pace = _average([
            _pace_seconds(step.get("pace_min")),
            _pace_seconds(step.get("pace_max")),
        ])

        if pace is None:
            return None

        easy = _pace_seconds(
            PaceService.easy(vdot)
        )
        marathon = _pace_seconds(
            PaceService.marathon(vdot)
        )
        threshold = _pace_seconds(
            PaceService.threshold(vdot)
        )
        interval = _pace_seconds(
            PaceService.interval(vdot)
        )

        if pace >= easy:
            return 1

        if pace >= marathon:
            return 2

        if pace >= threshold:
            return 3

        if pace >= interval:
            return 4

        return 5

    @staticmethod
    def _heart_rate_zone(
        step,
        max_hr,
        resting_hr,
    ):
        heart_rate = _average([
            step.get("heart_rate_min"),
            step.get("heart_rate_max"),
        ])

        if heart_rate is None:
            return None

        zones = HeartRateService.zones(
            max_hr,
            resting_hr,
        )

        for number in range(1, 6):
            low, high = zones[f"z{number}"]

            if low <= heart_rate <= high:
                return number

        if heart_rate < zones["z1"][0]:
            return 1

        return 5

    @staticmethod
    def _rpe_zone(step):
        rpe = _average([
            step.get("rpe_min"),
            step.get("rpe_max"),
        ])

        if rpe is None:
            return None

        if rpe <= 2:
            return 1

        if rpe <= 4:
            return 2

        if rpe <= 6:
            return 3

        if rpe <= 8:
            return 4

        return 5

    @staticmethod
    def _step_zone(
        step,
        evaluation,
    ):
        intensity_type = (
            step.get("intensity_type")
            or "pace"
        )

        if intensity_type == "pace":
            return SessionIntensityService._pace_zone(
                step,
                float(evaluation.vdot),
            )

        if intensity_type == "heart_rate":
            return (
                SessionIntensityService
                ._heart_rate_zone(
                    step,
                    int(evaluation.max_hr),
                    int(evaluation.resting_hr),
                )
            )

        if intensity_type == "rpe":
            return (
                SessionIntensityService
                ._rpe_zone(step)
            )

        return None

    @staticmethod
    def _step_weight(step):
        repetitions = max(
            1,
            int(step.get("repetitions") or 0),
        )
        group_repetitions = max(
            1,
            int(
                step.get(
                    "group_repetitions",
                )
                or 1
            ),
        )

        multiplier = (
            repetitions
            * group_repetitions
        )

        if (
            step.get("prescription_type")
            == "duration"
        ):
            return max(
                1,
                float(step.get("duration") or 0)
                * multiplier,
            )

        distance = float(
            step.get("distance") or 0
        )

        if step.get("distance_unit") == "m":
            distance /= 1000

        pace = _average([
            _pace_seconds(step.get("pace_min")),
            _pace_seconds(step.get("pace_max")),
        ])

        estimated_seconds_per_km = (
            pace
            if pace is not None
            else 360
        )

        return max(
            1,
            distance
            * estimated_seconds_per_km
            * multiplier,
        )

    @staticmethod
    def classify(
        steps,
        evaluation,
    ):
        if (
            evaluation is None
            or getattr(
                evaluation,
                "vdot",
                None,
            ) is None
        ):
            return "Avaliação necessária"

        if not steps:
            return "Avaliação necessária"

        primary_steps = [
            step
            for step in steps
            if str(
                step.get("type") or ""
            ).strip().lower()
            not in NON_PRIMARY_TYPES
        ]

        candidates = (
            primary_steps
            if primary_steps
            else steps
        )

        weighted = []

        for step in candidates:
            zone = (
                SessionIntensityService
                ._step_zone(
                    step,
                    evaluation,
                )
            )

            if zone is None:
                continue

            weighted.append((
                zone,
                SessionIntensityService
                ._step_weight(step),
            ))

        if not weighted:
            return "Regenerativo / leve"

        total_weight = sum(
            weight
            for _, weight in weighted
        )

        score = sum(
            zone * weight
            for zone, weight in weighted
        ) / total_weight

        zone_number = min(
            5,
            max(
                1,
                int(score + 0.5),
            ),
        )

        return INTENSITY_LABELS[
            zone_number
        ]
