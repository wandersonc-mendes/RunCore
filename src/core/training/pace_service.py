class PaceService:
    """
    Ritmos de treino baseados no VDOT.
    Valores temporários até integração
    com as tabelas oficiais de Jack Daniels.
    """

    @staticmethod
    def from_vdot(vdot: float) -> dict:

        if vdot <= 35:
            return {
                "easy": "06:30-07:00",
                "marathon": "06:00",
                "threshold": "05:40",
                "interval": "05:10",
                "repetition": "04:55",
            }

        if vdot <= 45:
            return {
                "easy": "05:50-06:20",
                "marathon": "05:20",
                "threshold": "05:00",
                "interval": "04:40",
                "repetition": "04:25",
            }

        if vdot <= 55:
            return {
                "easy": "05:00-05:30",
                "marathon": "04:35",
                "threshold": "04:20",
                "interval": "04:00",
                "repetition": "03:50",
            }

        return {
            "easy": "04:30-05:00",
            "marathon": "04:05",
            "threshold": "03:50",
            "interval": "03:35",
            "repetition": "03:25",
        }