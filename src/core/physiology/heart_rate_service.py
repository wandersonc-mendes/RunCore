class HeartRateService:
    """
    Cálculos relacionados à frequência cardíaca.
    """

    @staticmethod
    def reserve(max_hr: int, resting_hr: int) -> int:
        return max_hr - resting_hr

    @staticmethod
    def zone(max_hr: int, resting_hr: int, intensity: float) -> int:
        reserve = HeartRateService.reserve(
            max_hr,
            resting_hr,
        )

        return round(
            resting_hr + (reserve * intensity)
        )

    @staticmethod
    def zones(max_hr: int, resting_hr: int) -> dict:

        return {
            "z1": (
                HeartRateService.zone(max_hr, resting_hr, 0.50),
                HeartRateService.zone(max_hr, resting_hr, 0.60),
            ),
            "z2": (
                HeartRateService.zone(max_hr, resting_hr, 0.60),
                HeartRateService.zone(max_hr, resting_hr, 0.70),
            ),
            "z3": (
                HeartRateService.zone(max_hr, resting_hr, 0.70),
                HeartRateService.zone(max_hr, resting_hr, 0.80),
            ),
            "z4": (
                HeartRateService.zone(max_hr, resting_hr, 0.80),
                HeartRateService.zone(max_hr, resting_hr, 0.90),
            ),
            "z5": (
                HeartRateService.zone(max_hr, resting_hr, 0.90),
                HeartRateService.zone(max_hr, resting_hr, 1.00),
            ),
        }