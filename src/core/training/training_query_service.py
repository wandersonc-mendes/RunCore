from collections import defaultdict

from repositories.training_session_repository import (
    TrainingSessionRepository,
)


class TrainingQueryService:

    def __init__(self):

        self.repository = (
            TrainingSessionRepository()
        )

    def sessions_by_week(
        self,
        training_id: int,
    ):

        sessions = self.repository.list_by_training(
            training_id
        )

        weeks = defaultdict(list)

        for session in sessions:

            weeks[session.week].append(session)

        return dict(weeks)