class Vo2Service:
    """
    Cálculos de VO₂ Máx.
    """

    @staticmethod
    def from_1600(time_seconds: float) -> float:
        """
        Estima o VO₂ Máx a partir do teste de 1600 m.

        Parâmetro
        ---------
        time_seconds : tempo em segundos.

        Retorna
        -------
        VO₂ Máx estimado.
        """

        if time_seconds <= 0:
            return 0.0

        minutes = time_seconds / 60

        vo2 = 132.853 - (17.307 * minutes)

        return round(vo2, 1)