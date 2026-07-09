from core.physiology.pace_service import PaceService
from core.training.training_day import TrainingDay
from core.training.training_week import TrainingWeek
from core.training.workout_builder import WorkoutBuilder


class TrainingPlanService:

    @staticmethod
    def _build_day(
        name: str,
        workout=None,
        note: str = "",
        objective: str = "",
        priority: int = 0,
    ) -> TrainingDay:

        day = TrainingDay(name)

        day.notes = note
        day.objective = objective
        day.priority = priority

        if workout:
            day.add(workout)

        return day

    @staticmethod
    def generate_base_week(
        vdot: float,
        week_number: int = 1,
        long_run: float = 18,
        easy_run: float = 10,
        threshold_run: float = 8,
        interval_reps: int = 8,
    ) -> TrainingWeek:

        week = TrainingWeek(number=week_number)

        week.add(
            TrainingPlanService._build_day(
                name="Segunda",
                workout=WorkoutBuilder.easy(easy_run),
                note=f"Easy: {PaceService.easy(vdot)}",
                objective="Rodagem leve",
                priority=1,
            )
        )

        week.add(
            TrainingPlanService._build_day(
                name="Terça",
            )
        )

        week.add(
            TrainingPlanService._build_day(
                name="Quarta",
                workout=WorkoutBuilder.interval(
                    repetitions=interval_reps,
                    distance=400,
                    recovery=200,
                ),
                note=f"Interval: {PaceService.interval(vdot)}",
                objective="VO₂máx",
                priority=3,
            )
        )

        week.add(
            TrainingPlanService._build_day(
                name="Quinta",
            )
        )

        week.add(
            TrainingPlanService._build_day(
                name="Sexta",
                workout=WorkoutBuilder.threshold(
                    threshold_run
                ),
                note=f"Threshold: {PaceService.threshold(vdot)}",
                objective="Limiar",
                priority=2,
            )
        )

        week.add(
            TrainingPlanService._build_day(
                name="Sábado",
            )
        )

        week.add(
            TrainingPlanService._build_day(
                name="Domingo",
                workout=WorkoutBuilder.long(
                    long_run
                ),
                note=f"Marathon: {PaceService.marathon(vdot)}",
                objective="Resistência",
                priority=4,
            )
        )

        return week