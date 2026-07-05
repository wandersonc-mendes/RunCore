from dataclasses import dataclass, field

from core.training.training_day import TrainingDay


@dataclass
class TrainingWeek:

    number: int

    days: list[TrainingDay] = field(default_factory=list)

    notes: str = ""

    def add(self, day: TrainingDay):

        self.days.append(day)