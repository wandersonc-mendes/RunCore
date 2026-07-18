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

    objective: str = ""

    description: str = ""

    athlete_instructions: str = ""

    coach_notes: str = ""

    estimated_rpe: float | None = None

    estimated_duration: int | None = None

    estimated_distance: float | None = None

    methodology: str = "Jack Daniels"

    def has_distance(self) -> bool:

        return self.distance is not None

    def has_duration(self) -> bool:

        return self.duration is not None

    def is_interval(self) -> bool:

        return self.repetitions is not None

    def display_name(self) -> str:

        if self.repetitions:

            return (
                f"{self.repetitions} × "
                f"{self.distance:.0f} m"
            )

        if self.distance:

            return (
                f"{self.name} - "
                f"{self.distance:.1f} km"
            )

        if self.duration:

            return (
                f"{self.name} - "
                f"{self.duration} min"
            )

        return self.name