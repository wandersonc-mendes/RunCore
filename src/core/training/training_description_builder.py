from core.training.training_step_formatter import (
    TrainingStepFormatter,
)


class TrainingDescriptionBuilder:

    @staticmethod
    def build(steps) -> str:

        lines = []

        for step in steps:

            lines.append(
                TrainingStepFormatter.format(step)
            )

        return "\n\n".join(lines)