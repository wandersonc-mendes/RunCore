from datetime import date

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
    ):

        training = Training()

        training.athlete_id = athlete_id
        training.name = name
        training.methodology = methodology
        training.objective = objective
        training.target_distance = target_distance
        training.start_date = start_date
        training.target_date = target_date

        training = self.training_repository.create(
            training
        )

        if vdot is not None:
            self._generate_sessions(
                training.id,
                vdot,
                total_weeks,
                ipt_profile,
                target_distance=target_distance,
            )

        return training

    def regenerate_training(
        self,
        training_id: int,
        vdot: float,
        ipt_profile: str | None = None,
        total_weeks: int | None = None,
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
        target_distance = (
            training.target_distance
            if training
            else None
        )

        self.session_repository.delete_by_training(
            training_id
        )

        self._generate_sessions(
            training_id,
            vdot,
            total_weeks,
            ipt_profile,
            target_distance=target_distance,
        )

    def _generate_sessions(
        self,
        training_id: int,
        vdot: float,
        total_weeks: int,
        ipt_profile: str | None = None,
        target_distance: float | None = None,
    ):

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