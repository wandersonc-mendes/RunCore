from datetime import date, timedelta

from core.training.training_cycle_builder import (
    TrainingCycleBuilder,
)
from models.training import Training
from repositories.training_repository import (
    TrainingRepository,
)
from repositories.training_session_repository import (
    TrainingSessionRepository,
)


class TrainingPersistenceService:

    def __init__(self):

        self.training_repository = (
            TrainingRepository()
        )

        self.session_repository = (
            TrainingSessionRepository()
        )

    def create_training(
        self,
        athlete_id: int,
        vdot: float | None,
        name: str,
        methodology: str,
        objective: str,
        target_distance: float,
        start_date: date | None = None,
        target_date: date | None = None,
        total_weeks: int = 8,
        ipt_profile: str | None = None,
        training_days: list[int] | None = None,
    ):

        training = Training()

        training.athlete_id = athlete_id
        training.name = name
        training.methodology = methodology
        training.objective = objective
        training.target_distance = target_distance
        training.start_date = start_date or date.today()
        training.target_date = target_date

        training = self.training_repository.create(
            training
        )

        self._generate_sessions(
            training.id,
            vdot,
            total_weeks,
            ipt_profile,
            target_distance=target_distance,
            training_days=training_days,
            start_date=training.start_date,
        )

        return training

    def regenerate_training(
        self,
        training_id: int,
        vdot: float | None,
        ipt_profile: str | None = None,
        total_weeks: int | None = None,
        training_days: list[int] | None = None,
    ):

        sessions = (
            self.session_repository.list_by_training(
                training_id
            )
        )

        current_total_weeks = max(
            (
                session.week
                for session in sessions
            ),
            default=8,
        )

        total_weeks = total_weeks or current_total_weeks

        training = self.training_repository.get_by_id(
            training_id
        )

        if training is None:
            raise ValueError(
                "Planejamento não encontrado."
            )

        if training.start_date is None:
            training.start_date = date.today()
            training = self.training_repository.update(
                training
            )

        target_distance = training.target_distance

        self.session_repository.delete_by_training(
            training_id
        )

        self._generate_sessions(
            training_id,
            vdot,
            total_weeks,
            ipt_profile,
            target_distance=target_distance,
            training_days=training_days,
            start_date=training.start_date,
        )

    def _generate_sessions(
        self,
        training_id: int,
        vdot: float | None,
        total_weeks: int,
        ipt_profile: str | None = None,
        target_distance: float | None = None,
        training_days: list[int] | None = None,
        start_date: date | None = None,
    ):

        if vdot is None:
            cycle = TrainingCycleBuilder.initial(
                total_weeks=total_weeks,
                target_distance=target_distance,
                training_days=training_days,
            )
        else:
            cycle = TrainingCycleBuilder.base(
                vdot,
                total_weeks,
                ipt_profile=ipt_profile,
                target_distance=target_distance,
            )

        sessions = (
            TrainingCycleBuilder.to_training_sessions(
                training_id,
                cycle,
            )
        )

        if start_date is not None:
            cycle_week_monday = (
                start_date
                - timedelta(
                    days=start_date.weekday()
                )
            )

            scheduled_sessions = []

            for training_session in sessions:
                scheduled_date = (
                    cycle_week_monday
                    + timedelta(
                        weeks=max(
                            training_session.week - 1,
                            0,
                        ),
                        days=training_session.weekday,
                    )
                )

                if scheduled_date < start_date:
                    continue

                training_session.scheduled_date = (
                    scheduled_date
                )
                scheduled_sessions.append(
                    training_session
                )

            sessions = scheduled_sessions

        self.session_repository.create_many(
            sessions
        )

    def delete_training(
        self,
        training_id: int,
    ):

        self.training_repository.delete(
            training_id
        )