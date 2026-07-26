from core.training.training_cycle import TrainingCycle
from core.training.training_plan_service import (
    TrainingPlanService,
)
from models.training_session import TrainingSession


class TrainingCycleBuilder:

    @staticmethod
    def base(
        vdot: float,
        total_weeks: int = 8,
        ipt_profile: str | None = None,
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

        for week_number in range(
            1,
            total_weeks + 1,
        ):
            pattern_index = (
                week_number - 1
            ) % 4

            block_number = (
                week_number - 1
            ) // 4

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

            cycle.add(
                TrainingPlanService.generate_base_week(
                    vdot=vdot,
                    week_number=week_number,
                    long_run=long_run,
                    easy_run=easy_run,
                    threshold_run=threshold_run,
                    interval_reps=interval_reps,
                    ipt_profile=ipt_profile,
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

                session.planned_distance = (
                    workout.distance or 0
                )

                session.planned_duration = 0

                session.repetitions = (
                    workout.repetitions or 0
                )

                session.recovery = (
                    workout.recovery or 0
                )

                sessions.append(session)

        return sessions