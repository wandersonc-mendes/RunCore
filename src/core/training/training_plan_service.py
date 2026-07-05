from core.training.pace_service import PaceService
from core.training.training_day import TrainingDay
from core.training.training_week import TrainingWeek
from core.training.workout_builder import WorkoutBuilder


class TrainingPlanService:

    @staticmethod
    def generate_base_week(vdot: float) -> TrainingWeek:

        paces = PaceService.from_vdot(vdot)

        week = TrainingWeek(number=1)

        monday = TrainingDay("Segunda")
        monday.add(WorkoutBuilder.easy(10))
        monday.notes = (
            f"Easy: {paces['easy']}"
        )

        tuesday = TrainingDay("Terça")

        wednesday = TrainingDay("Quarta")
        wednesday.add(
            WorkoutBuilder.interval(
                repetitions=8,
                distance=400,
                recovery=200,
            )
        )
        wednesday.notes = (
            f"Interval: {paces['interval']}"
        )

        thursday = TrainingDay("Quinta")

        friday = TrainingDay("Sexta")
        friday.add(
            WorkoutBuilder.threshold(8)
        )
        friday.notes = (
            f"Threshold: {paces['threshold']}"
        )

        saturday = TrainingDay("Sábado")

        sunday = TrainingDay("Domingo")
        sunday.add(
            WorkoutBuilder.long(18)
        )
        sunday.notes = (
            f"Marathon: {paces['marathon']}"
        )

        week.add(monday)
        week.add(tuesday)
        week.add(wednesday)
        week.add(thursday)
        week.add(friday)
        week.add(saturday)
        week.add(sunday)

        return week