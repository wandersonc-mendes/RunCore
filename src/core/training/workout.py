from dataclasses import dataclass


@dataclass
class Workout:

    name: str

    zone: str

    distance: float | None = None

    duration: int | None = None

    repetitions: int | None = None

    interval: int | None = None

    recovery: int | None = None

    notes: str = ""