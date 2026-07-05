from dataclasses import dataclass, field

from core.training.training_week import TrainingWeek


@dataclass
class Microcycle:

    name: str

    objective: str

    weeks: list[TrainingWeek] = field(default_factory=list)

    notes: str = ""

    def add(self, week: TrainingWeek):

        self.weeks.append(week)