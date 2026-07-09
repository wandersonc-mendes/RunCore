from core.training.training_cycle import TrainingCycle
from core.training.training_plan_service import (
    TrainingPlanService,
)
from models.training_session import TrainingSession


class TrainingCycleBuilder:

    @staticmethod
    def base(vdot: float) -> TrainingCycle:

        cycle = TrainingCycle(
            name="Base"
        )

        cycle.add(
            TrainingPlanService.generate_base_week(
                vdot=vdot,
                week_number=1,
                long_run=18,
            )
        )

        cycle.add(
            TrainingPlanService.generate_base_week(
                vdot=vdot,
                week_number=2,
                long_run=20,
            )
        )

        cycle.add(
            TrainingPlanService.generate_base_week(
                vdot=vdot,
                week_number=3,
                long_run=22,
            )
        )

        cycle.add(
            TrainingPlanService.generate_base_week(
                vdot=vdot,
                week_number=4,
                long_run=16,
                interval_reps=6,
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
                session.distance = workout.distance or 0
                session.repetitions = workout.repetitions or 0
                session.recovery = workout.recovery or 0

                sessions.append(session)

        return sessions