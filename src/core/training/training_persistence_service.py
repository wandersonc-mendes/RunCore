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
        vdot: float,
        name: str,
        methodology: str,
        objective: str,
        target_distance: float,
    ):

        training = Training()

        training.athlete_id = athlete_id
        training.name = name
        training.methodology = methodology
        training.objective = objective
        training.target_distance = target_distance

        training = self.training_repository.create(
            training
        )

        self._generate_sessions(
            training.id,
            vdot,
        )

        return training

    def regenerate_training(
        self,
        training_id: int,
        vdot: float,
    ):

        sessions = (
            self.session_repository.list_by_training(
                training_id
            )
        )

        for session in sessions:

            self.session_repository.delete(
                session.id
            )

        self._generate_sessions(
            training_id,
            vdot,
        )

    def _generate_sessions(
        self,
        training_id: int,
        vdot: float,
    ):

        cycle = TrainingCycleBuilder.base(
            vdot
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