import math


class VdotService:
    """
    Implementação baseada nas equações de Jack Daniels.
    """

    @staticmethod
    def calculate(distance_m: float, time_seconds: float) -> float:

        if distance_m <= 0 or time_seconds <= 0:
            return 0.0

        # velocidade (m/min)
        velocity = distance_m / (time_seconds / 60)

        # tempo (min)
        minutes = time_seconds / 60

        # consumo de oxigênio para a velocidade
        vo2 = (
            -4.60
            + (0.182258 * velocity)
            + (0.000104 * velocity ** 2)
        )

        # percentual do VO₂ máximo sustentado
        percent = (
            0.8
            + (0.1894393 * math.exp(-0.012778 * minutes))
            + (0.2989558 * math.exp(-0.1932605 * minutes))
        )

        vdot = vo2 / percent

        return round(vdot, 1)

    @staticmethod
    def equivalent_vo2(vdot: float) -> float:

        return round(vdot, 1)