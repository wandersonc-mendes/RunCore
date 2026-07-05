class PredictionService:
    """
    Previsão de tempos baseada no VDOT.
    """

    @staticmethod
    def predict(vdot: float) -> dict:

        return {
            "5k": None,
            "10k": None,
            "21k": None,
            "42k": None,
        }