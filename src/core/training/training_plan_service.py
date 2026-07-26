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
        total_weeks: int = 8,
    ) -> TrainingWeek:

        week = TrainingWeek(number=week_number)

        normalized_profile = (ipt_profile or "").strip().lower()
        total_weeks = max(total_weeks, 1)
        phase_ratio = week_number / total_weeks
        block_position = (week_number - 1) % 4

        if phase_ratio <= 0.40:
            phase = "Base"
        elif phase_ratio <= 0.75:
            phase = "Desenvolvimento"
        elif phase_ratio <= 0.90:
            phase = "Específica"
        else:
            phase = "Polimento"

        work_volume = interval_reps * 400
        interval_distance = 400
        interval_name = "Intervalado"
        threshold_name = "Limiar"
        threshold_factor = 1.0

        if normalized_profile == "resistente":
            if phase == "Base":
                interval_distance = (200, 300, 400, 200)[block_position]
                interval_name = "Velocidade e economia"
                threshold_name = "Limiar controlado"
                threshold_factor = 0.85
            elif phase == "Desenvolvimento":
                interval_distance = (200, 300, 400, 300)[block_position]
                interval_name = "Intervalado curto"
                threshold_name = "Limiar"
                threshold_factor = 0.95
            elif phase == "Específica":
                interval_distance = (400, 600, 400, 300)[block_position]
                interval_name = "Intervalado específico"
                threshold_name = "Limiar específico"
            else:
                interval_distance = (200, 300, 200, 200)[block_position]
                interval_name = "Ativação de velocidade"
                threshold_name = "Limiar reduzido"
                threshold_factor = 0.65

        elif normalized_profile == "potente":
            if phase == "Base":
                interval_distance = (400, 600, 400, 600)[block_position]
                interval_name = "Intervalado moderado"
                threshold_name = "Limiar controlado"
                threshold_factor = 0.85
            elif phase == "Desenvolvimento":
                interval_distance = (800, 1000, 800, 600)[block_position]
                interval_name = "Intervalado longo"
                threshold_name = "Limiar sustentado"
            elif phase == "Específica":
                interval_distance = (1000, 1200, 800, 600)[block_position]
                interval_name = "Resistência de velocidade"
                threshold_name = "Limiar específico"
                threshold_factor = 1.05
            else:
                interval_distance = (400, 600, 400, 400)[block_position]
                interval_name = "Ativação intervalada"
                threshold_name = "Limiar reduzido"
                threshold_factor = 0.65

        elif phase == "Polimento":
            interval_name = "Intervalado reduzido"
            threshold_name = "Limiar reduzido"
            threshold_factor = 0.65

        adjusted_interval_reps = max(1, round(work_volume / interval_distance))

        if phase == "Polimento":
            adjusted_interval_reps = max(
                2,
                round(adjusted_interval_reps * 0.65),
            )

        interval_recovery = max(100, interval_distance // 2)

        interval_workout = WorkoutBuilder.interval(
            repetitions=adjusted_interval_reps,
            distance=interval_distance,
            recovery=interval_recovery,
        )
        interval_workout.name = interval_name

        threshold_workout = WorkoutBuilder.threshold(
            round(threshold_run * threshold_factor, 1)
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