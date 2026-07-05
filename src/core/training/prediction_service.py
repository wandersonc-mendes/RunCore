class PredictionService:
    """
    Previsão de tempos baseada no VDOT.
    Valores temporários.
    """

    @staticmethod
    def from_vdot(vdot: float) -> dict:

        if vdot <= 35:
            return {
                "5k": "32:00",
                "10k": "1:07:00",
                "21k": "2:28:00",
                "42k": "5:10:00",
            }

        if vdot <= 45:
            return {
                "5k": "25:00",
                "10k": "52:00",
                "21k": "1:55:00",
                "42k": "4:05:00",
            }

        if vdot <= 55:
            return {
                "5k": "20:00",
                "10k": "41:30",
                "21k": "1:31:00",
                "42k": "3:12:00",
            }

        return {
            "5k": "17:00",
            "10k": "35:20",
            "21k": "1:18:00",
            "42k": "2:44:00",
        }