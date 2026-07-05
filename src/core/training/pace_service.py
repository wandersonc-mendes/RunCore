class PaceService:
    """
    Geração dos ritmos de treino.
    """

    @staticmethod
    def from_vdot(vdot: float) -> dict:

        return {
            "easy": None,
            "marathon": None,
            "threshold": None,
            "interval": None,
            "repetition": None,
        }ok