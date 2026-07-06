import math

from core.physiology.running_math import RunningMath


class VdotService:
    """
    Implementação baseada nas equações de Jack Daniels.
    """

    @staticmethod
    def calculate(
        distance_m: float,
        time_seconds: float,
    ) -> float:

        if distance_m <= 0 or time_seconds <= 0:
            return 0.0

        velocity = RunningMath.velocity(
            distance_m,
            time_seconds,
        )

        minutes = time_seconds / 60

        vo2 = (
            -4.60
            + (0.182258 * velocity)
            + (0.000104 * velocity ** 2)
        )

        percent = (
            0.8
            + (
                0.1894393
                * math.exp(-0.012778 * minutes)
            )
            + (
                0.2989558
                * math.exp(-0.1932605 * minutes)
            )
        )

        return round(vo2 / percent, 1)

    @staticmethod
    def equivalent_vo2(vdot: float) -> float:

        return round(vdot, 1)