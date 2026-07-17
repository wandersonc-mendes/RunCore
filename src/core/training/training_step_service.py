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
                "distance": item.distance,
                "repetitions": item.repetitions,
                "pace_min": item.pace_min,
                "pace_max": item.pace_max,
                "notes": item.notes,
            })

        return result

    def save(self, session_id, steps):

        self.repository.delete_by_session(
            session_id
        )

        objects = []

        for order, item in enumerate(
            steps,
            start=1,
        ):

            step = TrainingStep()

            step.session_id = session_id
            step.order = order
            step.type = item["type"]
            step.distance = item["distance"]
            step.duration = 0
            step.repetitions = item["repetitions"]
            step.recovery = ""
            step.pace_min = item["pace_min"]
            step.pace_max = item["pace_max"]
            step.notes = item["notes"]

            objects.append(step)

        self.repository.create_many(
            objects
        )