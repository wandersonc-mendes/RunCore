from models.training_step import TrainingStep
from repositories.training_step_repository import (
    TrainingStepRepository,
)


class TrainingStepService:

    def __init__(self):

        self.repository = (
            TrainingStepRepository()
        )

    def load(self, session_id):

        items = self.repository.list_by_session(
            session_id
        )

        result = []

        for item in items:

            result.append({
                "type": item.type,
                "prescription_type": (
                    item.prescription_type
                    or "distance"
                ),
                "intensity_type": (
                    item.intensity_type
                    or "pace"
                ),
                "distance": item.distance,
                "distance_unit": item.distance_unit,
                "duration": item.duration,
                "repetitions": item.repetitions,
                "recovery": item.recovery,
                "pace_min": item.pace_min,
                "pace_max": item.pace_max,
                "heart_rate_min": item.heart_rate_min,
                "heart_rate_max": item.heart_rate_max,
                "rpe_min": item.rpe_min,
                "rpe_max": item.rpe_max,
                "notes": item.notes,
            })

        return result

    def save(self, session_id, steps):
        objects = []

        for order, item in enumerate(
            steps,
            start=1,
        ):

            step = TrainingStep()

            step.session_id = session_id
            step.order = order
            step.type = item["type"]

            prescription_type = item.get(
                "prescription_type",
                "distance",
            )
            intensity_type = item.get(
                "intensity_type",
                "pace",
            )

            step.prescription_type = prescription_type
            step.intensity_type = intensity_type
            step.distance = (
                float(item.get("distance") or 0)
                if prescription_type == "distance"
                else 0
            )
            step.distance_unit = item.get(
                "distance_unit",
                "m" if item.get("repetitions") else "km",
            )
            step.duration = (
                int(item.get("duration") or 0)
                if prescription_type == "duration"
                else 0
            )
            step.repetitions = item["repetitions"]
            step.recovery = item.get("recovery", "")
            step.pace_min = (
                item.get("pace_min", "")
                if intensity_type == "pace"
                else ""
            )
            step.pace_max = (
                item.get("pace_max", "")
                if intensity_type == "pace"
                else ""
            )
            step.heart_rate_min = (
                item.get("heart_rate_min")
                if intensity_type == "heart_rate"
                else None
            )
            step.heart_rate_max = (
                item.get("heart_rate_max")
                if intensity_type == "heart_rate"
                else None
            )
            step.rpe_min = (
                item.get("rpe_min")
                if intensity_type == "rpe"
                else None
            )
            step.rpe_max = (
                item.get("rpe_max")
                if intensity_type == "rpe"
                else None
            )
            step.notes = item["notes"]

            objects.append(step)

        self.repository.replace_by_session(
            session_id,
            objects
        )
