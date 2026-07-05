from dataclasses import dataclass, field

from core.training.training_cycle import TrainingCycle


@dataclass
class Mesocycle:

    name: str

    objective: str

    cycles: list[TrainingCycle] = field(default_factory=list)

    notes: str = ""

    def add(self, cycle: TrainingCycle):

        self.cycles.append(cycle)