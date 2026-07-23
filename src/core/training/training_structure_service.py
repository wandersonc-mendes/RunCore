from core.training.training_step_service import (
    TrainingStepService,
)


class TrainingStructureService:

    def __init__(self):

        self.step_service = (
            TrainingStepService()
        )

    def load(self, session_id):

        return self.step_service.load(
            session_id
        )

    def save(self, session_id, steps):

        self.validate(steps)

        self.step_service.save(
            session_id,
            steps,
        )

    def add_step(self, steps, step):

        steps.append(step)

        return steps

    def remove_step(self, steps, index):

        if 0 <= index < len(steps):
            del steps[index]

        return steps

    def move_up(self, steps, index):

        if index <= 0:
            return steps

        steps[index - 1], steps[index] = (
            steps[index],
            steps[index - 1],
        )

        return steps

    def move_down(self, steps, index):

        if index >= len(steps) - 1:
            return steps

        steps[index + 1], steps[index] = (
            steps[index],
            steps[index + 1],
        )

        return steps

    def validate(self, steps):

        if not steps:
            return

        for i, step in enumerate(steps, start=1):

            if not step["type"]:
                raise ValueError(
                    f"Etapa {i}: tipo obrigatório."
                )

            if step["distance"] < 0:
                raise ValueError(
                    f"Etapa {i}: distância inválida."
                )

            if step["repetitions"] < 0:
                raise ValueError(
                    f"Etapa {i}: repetições inválidas."
                )