from dataclasses import dataclass, field

from core.training.training_week import TrainingWeek


@dataclass
class TrainingCycle:

    name: str

    weeks: list[TrainingWeek] = field(default_factory=list)

    notes: str = ""

    target_distance: float = 0.0

    target_date: str = ""

    methodology: str = "Jack Daniels"

    def add(self, week: TrainingWeek):

        self.weeks.append(week)

    @property
    def total_weeks(self) -> int:

        return len(self.weeks)

    @property
    def total_distance(self) -> float:

        return sum(
            week.total_distance
            for week in self.weeks
        )

    def week(self, number: int) -> TrainingWeek | None:

        for week in self.weeks:

            if week.number == number:
                return week

        return None