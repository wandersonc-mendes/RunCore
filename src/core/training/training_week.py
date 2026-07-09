from dataclasses import dataclass, field

from core.training.training_day import TrainingDay


@dataclass
class TrainingWeek:

    number: int

    days: list[TrainingDay] = field(default_factory=list)

    notes: str = ""

    def add(self, day: TrainingDay):

        self.days.append(day)

    @property
    def training_days(self) -> list[TrainingDay]:

        return [
            day
            for day in self.days
            if day.workouts
        ]

    @property
    def rest_days(self) -> list[TrainingDay]:

        return [
            day
            for day in self.days
            if not day.workouts
        ]

    @property
    def quality_days(self) -> list[TrainingDay]:

        quality = []

        for day in self.training_days:

            if any(
                workout.zone in (
                    "Threshold",
                    "Interval",
                    "Repetition",
                )
                for workout in day.workouts
            ):
                quality.append(day)

        return quality

    @property
    def long_run(self) -> TrainingDay | None:

        for day in self.training_days:

            if any(
                workout.name == "Longão"
                for workout in day.workouts
            ):
                return day

        return None

    @property
    def total_distance(self) -> float:

        total = 0.0

        for day in self.training_days:

            for workout in day.workouts:

                if workout.distance:
                    total += workout.distance

        return total

    @property
    def total_duration(self) -> int:

        return sum(
            day.estimated_duration
            for day in self.training_days
        )