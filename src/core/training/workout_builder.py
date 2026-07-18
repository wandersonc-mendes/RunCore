from core.education.workout_knowledge import (
    WorkoutKnowledge,
)
from core.training.training_zone import TrainingZone
from core.training.workout import Workout


class WorkoutBuilder:

    @staticmethod
    def _build(
        name: str,
        zone: str,
        **kwargs,
    ):

        knowledge = (
            WorkoutKnowledge.get(name) or {}
        )

        return Workout(
            name=name,
            zone=zone,
            objective=knowledge.get(
                "objective",
                "",
            ),
            description=knowledge.get(
                "objective",
                "",
            ),
            athlete_instructions=knowledge.get(
                "perception",
                "",
            ),
            **kwargs,
        )

    @staticmethod
    def easy(distance: float):

        return WorkoutBuilder._build(
            name="Corrida Fácil",
            zone=TrainingZone.EASY.value,
            distance=distance,
            estimated_rpe=3,
        )

    @staticmethod
    def marathon(distance: float):

        return WorkoutBuilder._build(
            name="Ritmo de Maratona",
            zone=TrainingZone.MARATHON.value,
            distance=distance,
            estimated_rpe=6,
        )

    @staticmethod
    def threshold(distance: float):

        return WorkoutBuilder._build(
            name="Limiar",
            zone=TrainingZone.THRESHOLD.value,
            distance=distance,
            estimated_rpe=7,
        )

    @staticmethod
    def interval(
        repetitions: int,
        distance: float,
        recovery: int,
    ):

        return WorkoutBuilder._build(
            name="Intervalado",
            zone=TrainingZone.INTERVAL.value,
            repetitions=repetitions,
            distance=distance,
            recovery=recovery,
            estimated_rpe=8,
        )

    @staticmethod
    def repetition(
        repetitions: int,
        distance: float,
        recovery: int,
    ):

        return WorkoutBuilder._build(
            name="Repetição",
            zone=TrainingZone.REPETITION.value,
            repetitions=repetitions,
            distance=distance,
            recovery=recovery,
            estimated_rpe=9,
        )

    @staticmethod
    def long(distance: float):

        return WorkoutBuilder._build(
            name="Longão",
            zone=TrainingZone.MARATHON.value,
            distance=distance,
            estimated_rpe=5,
        )