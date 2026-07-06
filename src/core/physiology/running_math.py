class RunningMath:

    @staticmethod
    def velocity(distance_m: float, time_seconds: float) -> float:

        if distance_m <= 0 or time_seconds <= 0:
            return 0.0

        return distance_m / (time_seconds / 60)

    @staticmethod
    def pace_seconds_per_km(
        distance_m: float,
        time_seconds: float,
    ) -> float:

        if distance_m <= 0:
            return 0.0

        return time_seconds / (distance_m / 1000)

    @staticmethod
    def pace_text(seconds: float) -> str:

        minutes = int(seconds // 60)
        seconds = int(round(seconds % 60))

        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def kmh_from_pace(seconds: float) -> float:

        if seconds <= 0:
            return 0

        return round(
            3600 / seconds,
            2,
        )