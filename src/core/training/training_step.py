from dataclasses import dataclass


@dataclass(slots=True)
class TrainingStep:

    order: int

    title: str

    instruction: str

    distance: float | None = None

    duration: int | None = None

    repetitions: int | None = None

    interval_distance: float | None = None

    interval_duration: int | None = None

    pace_min: str = ""

    pace_max: str = ""

    speed_min: float | None = None

    speed_max: float | None = None

    recovery: str = ""

    notes: str = ""

    cadence: str = ""

    incline: str = ""

    heart_rate: str = ""

    terrain: str = ""

    def is_interval(self):

        return self.repetitions is not None