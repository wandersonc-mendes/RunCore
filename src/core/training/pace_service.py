class PaceService:
    """
    Ritmos de treino baseados no VDOT.
    """

    @staticmethod
    def calculate(vdot: float) -> dict:

        return {
            "easy": (
                max(vdot - 30, 0),
                max(vdot - 20, 0),
            ),
            "marathon": (
                max(vdot - 15, 0),
                max(vdot - 10, 0),
            ),
            "threshold": (
                max(vdot - 8, 0),
                max(vdot - 5, 0),
            ),
            "interval": (
                max(vdot - 3, 0),
                max(vdot - 1, 0),
            ),
            "repetition": (
                vdot,
                vdot + 2,
            ),
        }