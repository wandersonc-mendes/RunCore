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
        target_distance: float | None = None,
    ) -> TrainingWeek:

        week = TrainingWeek(number=week_number)

        normalized_profile = (ipt_profile or "").strip().lower()
        total_weeks = max(total_weeks, 1)
        is_race_week = week_number == total_weeks
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

        target = float(target_distance or 10)

        if target <= 5:
            race_group = "5k"
            volume_factor = 0.90
        elif target <= 10:
            race_group = "10k"
            volume_factor = 1.00
        elif target <= 21.1:
            race_group = "half"
            volume_factor = 1.15
        else:
            race_group = "marathon"
            volume_factor = 1.25

        base_work_volume = interval_reps * 400
        phase_volume_factor = {
            "Base": 0.90,
            "Desenvolvimento": 1.10,
            "Específica": 1.20,
            "Polimento": 0.60,
        }[phase]

        work_volume = max(
            1600,
            round(
                base_work_volume
                * volume_factor
                * phase_volume_factor,
                -2,
            ),
        )

        interval_catalog = {
            "equilibrado": {
                "Base": {
                    "distances": (200, 400, 500, 600),
                    "name": "Economia e velocidade",
                },
                "Desenvolvimento": {
                    "distances": (800, 1000, 1200, 600),
                    "name": "Intervalado progressivo",
                },
                "Específica": {
                    "5k": (1000, 1200, 800, 1600),
                    "10k": (1000, 1600, 2000, 1200),
                    "half": (1200, 1600, 2000, 1000),
                    "marathon": (1600, 2000, 1200, 1000),
                    "name": "Intervalado específico",
                },
                "Polimento": {
                    "distances": (200, 400, 600, 300),
                    "name": "Ativação neuromuscular",
                },
            },
            "resistente": {
                "Base": {
                    "distances": (200, 300, 400, 500),
                    "name": "Velocidade e economia",
                },
                "Desenvolvimento": {
                    "distances": (400, 500, 600, 800),
                    "name": "Intervalado curto",
                },
                "Específica": {
                    "5k": (600, 800, 1000, 500),
                    "10k": (800, 1000, 1200, 600),
                    "half": (1000, 1200, 1600, 800),
                    "marathon": (1000, 1600, 2000, 800),
                    "name": "Resistência de velocidade",
                },
                "Polimento": {
                    "distances": (200, 300, 400, 200),
                    "name": "Ativação de velocidade",
                },
            },
            "potente": {
                "Base": {
                    "distances": (500, 600, 800, 400),
                    "name": "Intervalado moderado",
                },
                "Desenvolvimento": {
                    "distances": (800, 1000, 1200, 1600),
                    "name": "Intervalado longo",
                },
                "Específica": {
                    "5k": (1000, 1200, 1600, 800),
                    "10k": (1200, 1600, 2000, 1000),
                    "half": (1600, 2000, 1200, 1000),
                    "marathon": (2000, 1600, 1200, 1000),
                    "name": "Sustentação de velocidade",
                },
                "Polimento": {
                    "distances": (400, 600, 500, 300),
                    "name": "Ativação intervalada",
                },
            },
        }

        profile_key = (
            normalized_profile
            if normalized_profile in interval_catalog
            else "equilibrado"
        )

        phase_catalog = interval_catalog[
            profile_key
        ][phase]

        if phase == "Específica":
            interval_distances = phase_catalog[
                race_group
            ]
        else:
            interval_distances = phase_catalog[
                "distances"
            ]

        interval_distance = interval_distances[
            block_position
        ]
        interval_name = phase_catalog["name"]

        threshold_name = {
            "Base": "Limiar controlado",
            "Desenvolvimento": "Limiar sustentado",
            "Específica": "Limiar específico",
            "Polimento": "Limiar reduzido",
        }[phase]

        threshold_factor = {
            "Base": 0.85,
            "Desenvolvimento": 1.00,
            "Específica": 1.05,
            "Polimento": 0.65,
        }[phase]

        adjusted_interval_reps = max(
            1,
            round(work_volume / interval_distance),
        )

        if phase == "Polimento":
            adjusted_interval_reps = max(
                2,
                round(adjusted_interval_reps * 0.65),
            )

        if is_race_week:
            adjusted_interval_reps = min(
                adjusted_interval_reps,
                4,
            )
            interval_name = "Ativação pré-prova"
            threshold_name = "Corrida leve pré-prova"
            threshold_factor = 0.45

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

        final_workout = WorkoutBuilder.long(
            target_distance
            if is_race_week and target_distance
            else long_run
        )

        if is_race_week and target_distance:
            final_workout.name = "Prova-alvo"
            final_note = (
                "Executar a prova conforme a estratégia definida "
                "com o treinador."
            )
            final_objective = "Competição"
        else:
            final_note = (
                f"Marathon: {PaceService.marathon(vdot)}"
            )
            final_objective = "Resistência"

        week.add(
            TrainingPlanService._build_day(
                name="Domingo",
                workout=final_workout,
                note=final_note,
                objective=final_objective,
                priority=4,
            )
        )

        return week