from dataclasses import dataclass, field

from core.training.workout import Workout


@dataclass
class TrainingDay:

    day: str

    workouts: list[Workout] = field(default_factory=list)

    notes: str = ""

    objective: str = ""

    priority: int = 0

    estimated_duration: int = 0

    optional: bool = False

    completed: bool = False

    def add(self, workout: Workout):

        self.workouts.append(workout)