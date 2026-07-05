from core.training.training_zone import TrainingZone
from core.training.workout import Workout


class WorkoutBuilder:

    @staticmethod
    def easy(distance: float):

        return Workout(
            name="Corrida Fácil",
            zone=TrainingZone.EASY.value,
            distance=distance,
        )

    @staticmethod
    def marathon(distance: float):

        return Workout(
            name="Ritmo de Maratona",
            zone=TrainingZone.MARATHON.value,
            distance=distance,
        )

    @staticmethod
    def threshold(distance: float):

        return Workout(
            name="Limiar",
            zone=TrainingZone.THRESHOLD.value,
            distance=distance,
        )

    @staticmethod
    def interval(
        repetitions: int,
        distance: float,
        recovery: int,
    ):

        return Workout(
            name="Intervalado",
            zone=TrainingZone.INTERVAL.value,
            repetitions=repetitions,
            distance=distance,
            recovery=recovery,
        )

    @staticmethod
    def repetition(
        repetitions: int,
        distance: float,
        recovery: int,
    ):

        return Workout(
            name="Repetição",
            zone=TrainingZone.REPETITION.value,
            repetitions=repetitions,
            distance=distance,
            recovery=recovery,
        )

    @staticmethod
    def long(distance: float):

        return Workout(
            name="Longão",
            zone=TrainingZone.MARATHON.value,
            distance=distance,
        )