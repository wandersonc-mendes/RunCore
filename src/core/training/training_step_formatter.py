from core.training.training_step import (
    TrainingStep,
)


class TrainingStepFormatter:

    @staticmethod
    def format(step: TrainingStep) -> str:

        text = (
            f"{step.order}. "
            f"{step.instruction} "
        )

        if step.is_interval():

            text += (
                f"{step.repetitions} × "
                f"{int(step.interval_distance)} m\n"
            )

        elif step.distance:

            text += (
                f"{step.distance:.3f} km\n"
            )

        elif step.duration:

            text += (
                f"{step.duration} min\n"
            )

        if step.pace_min:

            text += (
                f"Pace ({step.pace_min} a "
                f"{step.pace_max} min/km)"
            )

        if (
            step.speed_min is not None
            and step.speed_max is not None
        ):

            text += (
                f"\nVelocidade "
                f"({step.speed_min:.2f} a "
                f"{step.speed_max:.2f} km/h)"
            )

        if step.heart_rate:

            text += (
                f"\nFC: {step.heart_rate}"
            )

        if step.cadence:

            text += (
                f"\nCadência: {step.cadence}"
            )

        if step.recovery:

            text += (
                f"\nRecuperação: {step.recovery}"
            )

        if step.terrain:

            text += (
                f"\nTerreno: {step.terrain}"
            )

        if step.incline:

            text += (
                f"\nInclinação: {step.incline}"
            )

        if step.notes:

            text += (
                f"\n{step.notes}"
            )

        return text