from dataclasses import dataclass, field

from core.training.workout import Workout


@dataclass
class TrainingDay:

    day: str

    workouts: list[Workout] = field(default_factory=list)

    notes: str = ""

    def add(self, workout: Workout):

        self.workouts.append(workout)