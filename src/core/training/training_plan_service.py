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
        ipt_profile: str | None = None,
    ) -> TrainingWeek:

        week = TrainingWeek(number=week_number)

        normalized_profile = (ipt_profile or "").strip().lower()
        interval_distance = 400
        interval_recovery = 200
        adjusted_interval_reps = interval_reps
        interval_name = "Intervalado"
        threshold_name = "Limiar"

        if normalized_profile == "resistente":
            interval_distance = 200
            interval_recovery = 100
            adjusted_interval_reps = interval_reps * 2
            interval_name = "Intervalado curto"
            threshold_name = "Limiar controlado"
        elif normalized_profile == "potente":
            interval_distance = 800
            interval_recovery = 400
            adjusted_interval_reps = max(1, interval_reps // 2)
            interval_name = "Intervalado longo"
            threshold_name = "Limiar sustentado"

        interval_workout = WorkoutBuilder.interval(
            repetitions=adjusted_interval_reps,
            distance=interval_distance,
            recovery=interval_recovery,
        )
        interval_workout.name = interval_name

        threshold_workout = WorkoutBuilder.threshold(
            threshold_run
        )
        threshold_workout.name = threshold_name

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
                workout=interval_workout,
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
                workout=threshold_workout,
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