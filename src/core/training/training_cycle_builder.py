from core.training.training_cycle import TrainingCycle
from core.training.training_plan_service import (
    TrainingPlanService,
)
from core.training.training_day import TrainingDay
from core.training.training_week import TrainingWeek
from core.training.workout_builder import WorkoutBuilder
from core.training.training_zone import TrainingZone
from models.training_session import TrainingSession


class TrainingCycleBuilder:

    @staticmethod
    def initial(
        total_weeks: int = 8,
        target_distance: float | None = None,
        training_days: list[int] | None = None,
    ) -> TrainingCycle:

        cycle = TrainingCycle(
            name="Base inicial sem avaliação"
        )

        total_weeks = max(1, total_weeks)
        target = max(
            3.0,
            float(target_distance or 5.0),
        )

        selected_days = sorted(
            set(training_days or [0, 2, 5])
        )

        if (
            len(selected_days) != 3
            or any(day < 0 or day > 6 for day in selected_days)
        ):
            raise ValueError(
                "Selecione exatamente 3 dias diferentes da semana."
            )

        weekday_names = [
            "Segunda",
            "Terça",
            "Quarta",
            "Quinta",
            "Sexta",
            "Sábado",
            "Domingo",
        ]

        for week_number in range(1, total_weeks + 1):
            block_position = (week_number - 1) % 4
            progression = ((week_number - 1) // 4) * 0.5

            easy_distance = min(
                target,
                3.0 + progression + (block_position * 0.25),
            )
            long_distance = min(
                max(4.0, target),
                4.0 + progression + (block_position * 0.5),
            )

            if block_position == 3:
                easy_distance = round(easy_distance * 0.85, 1)
                long_distance = round(long_distance * 0.85, 1)

            if week_number == total_weeks:
                easy_distance = round(easy_distance * 0.75, 1)
                long_distance = round(long_distance * 0.70, 1)

            week = TrainingWeek(number=week_number)

            workouts_by_day = {
                selected_days[0]: {
                    "workout": WorkoutBuilder.easy(
                        round(max(2.0, easy_distance), 1)
                    ),
                    "objective": "Adaptação aeróbica inicial",
                    "notes": (
                        "Esforço confortável. Ritmo livre, guiado pela "
                        "percepção e pelo teste da conversa."
                    ),
                },
                selected_days[1]: {
                    "workout": WorkoutBuilder.easy(
                        round(max(2.0, easy_distance), 1)
                    ),
                    "objective": "Continuidade e adaptação",
                    "notes": (
                        "Manter esforço leve. Caminhar quando necessário; "
                        "não perseguir ritmo."
                    ),
                },
                selected_days[2]: {
                    "workout": WorkoutBuilder.long(
                        round(max(3.0, long_distance), 1),
                        zone=TrainingZone.EASY.value,
                    ),
                    "objective": "Resistência aeróbica leve",
                    "notes": (
                        "Sessão contínua confortável. Pode alternar corrida "
                        "e caminhada. Sem alvo de pace até avaliação."
                    ),
                },
            }

            for weekday, day_name in enumerate(weekday_names):
                day = TrainingDay(day_name)
                prescription = workouts_by_day.get(weekday)

                if prescription is not None:
                    day.objective = prescription["objective"]
                    day.notes = prescription["notes"]
                    day.add(prescription["workout"])

                week.add(day)

            cycle.add(week)

        return cycle

    @staticmethod
    def base(
        vdot: float,
        total_weeks: int = 8,
        ipt_profile: str | None = None,
        target_distance: float | None = None,
    ) -> TrainingCycle:

        cycle = TrainingCycle(
            name="Base"
        )

        total_weeks = max(
            1,
            total_weeks,
        )

        long_run_pattern = [
            18,
            20,
            22,
            16,
        ]

        interval_pattern = [
            8,
            8,
            8,
            6,
        ]

        easy_run_pattern = [
            10,
            11,
            12,
            9,
        ]

        threshold_pattern = [
            8,
            8,
            9,
            6,
        ]

        peak_block = max(
            0,
            ((max(total_weeks - 3, 1) - 1) // 4),
        )

        for week_number in range(
            1,
            total_weeks + 1,
        ):
            pattern_index = (
                week_number - 1
            ) % 4

            raw_block_number = (
                week_number - 1
            ) // 4

            block_number = min(
                raw_block_number,
                peak_block,
            )

            long_run = (
                long_run_pattern[pattern_index]
                + block_number
            )

            easy_run = (
                easy_run_pattern[pattern_index]
                + (block_number * 0.5)
            )

            threshold_run = (
                threshold_pattern[pattern_index]
                + (block_number * 0.5)
            )

            interval_reps = (
                interval_pattern[pattern_index]
            )

            weeks_remaining = total_weeks - week_number

            if weeks_remaining == 2:
                volume_factor = 0.75
            elif weeks_remaining == 1:
                volume_factor = 0.55
            elif weeks_remaining == 0:
                volume_factor = 0.35
            else:
                volume_factor = 1.0

            easy_run = round(
                easy_run * volume_factor,
                1,
            )
            threshold_run = round(
                threshold_run * volume_factor,
                1,
            )
            long_run = round(
                long_run * volume_factor,
                1,
            )
            interval_reps = max(
                2,
                round(interval_reps * volume_factor),
            )

            cycle.add(
                TrainingPlanService.generate_base_week(
                    vdot=vdot,
                    week_number=week_number,
                    long_run=long_run,
                    easy_run=easy_run,
                    threshold_run=threshold_run,
                    interval_reps=interval_reps,
                    ipt_profile=ipt_profile,
                    total_weeks=total_weeks,
                    target_distance=target_distance,
                )
            )

        return cycle

    @staticmethod
    def to_training_sessions(
        training_id: int,
        cycle: TrainingCycle,
    ) -> list[TrainingSession]:

        sessions = []

        weekday = {
            "Segunda": 0,
            "Terça": 1,
            "Quarta": 2,
            "Quinta": 3,
            "Sexta": 4,
            "Sábado": 5,
            "Domingo": 6,
        }

        for week in cycle.weeks:

            for day in week.days:

                if not day.workouts:
                    continue

                workout = day.workouts[0]

                session = TrainingSession()

                session.training_id = training_id
                session.week = week.number
                session.weekday = weekday[day.day]
                session.workout_name = workout.name
                session.zone = workout.zone

                repetitions = int(
                    workout.repetitions or 0
                )
                step_distance = float(
                    workout.distance or 0
                )
                recovery_distance = float(
                    workout.recovery or 0
                )

                if repetitions > 0:
                    session.planned_distance = round(
                        (
                            (
                                step_distance
                                + recovery_distance
                            )
                            * repetitions
                        )
                        / 1000,
                        3,
                    )
                else:
                    session.planned_distance = (
                        step_distance
                    )

                session._generated_step_distance = (
                    step_distance
                )

                session.planned_duration = 0

                session.repetitions = repetitions

                session.recovery = (
                    workout.recovery or 0
                )

                sessions.append(session)

        return sessions