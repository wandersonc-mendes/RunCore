from sqlalchemy import delete, select

from database.database import SessionLocal
from models.training_session import (
    TrainingSession,
)
from models.training_step import TrainingStep


class TrainingSessionRepository:

    def create(self, session_data):

        session = SessionLocal()

        session.add(session_data)

        session.commit()

        session.refresh(session_data)

        session.close()

        return session_data

    def create_many(self, sessions):

        session = SessionLocal()

        session.add_all(sessions)

        session.commit()

        session.close()

    def get_by_id(self, session_id):

        session = SessionLocal()

        item = session.get(
            TrainingSession,
            session_id,
        )

        session.close()

        return item

    def list_by_training(
        self,
        training_id,
    ):

        session = SessionLocal()

        result = session.scalars(
            select(TrainingSession)
            .where(
                TrainingSession.training_id == training_id
            )
            .order_by(
                TrainingSession.week,
                TrainingSession.weekday,
            )
        ).all()

        session.close()

        return result

    def update(self, session_data):

        session = SessionLocal()

        session_data = session.merge(
            session_data
        )

        session.commit()

        session.refresh(session_data)

        session.close()

        return session_data

    def delete_by_training(self, training_id):
        session = SessionLocal()

        try:
            session_ids = (
                select(TrainingSession.id)
                .where(
                    TrainingSession.training_id
                    == training_id
                )
            )

            session.execute(
                delete(TrainingStep)
                .where(
                    TrainingStep.session_id.in_(
                        session_ids
                    )
                )
            )

            session.execute(
                delete(TrainingSession)
                .where(
                    TrainingSession.training_id
                    == training_id
                )
            )

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_regenerable_by_training(
        self,
        training_id,
        today,
    ):
        session = SessionLocal()

        try:
            regenerable_ids = (
                select(TrainingSession.id)
                .where(
                    TrainingSession.training_id
                    == training_id,
                    TrainingSession.manual_override.is_(
                        False
                    ),
                    TrainingSession.completed.is_(
                        False
                    ),
                    (
                        TrainingSession.scheduled_date
                        >= today
                    )
                    | (
                        TrainingSession.scheduled_date
                        .is_(None)
                    ),
                )
            )

            session.execute(
                delete(TrainingStep)
                .where(
                    TrainingStep.session_id.in_(
                        regenerable_ids
                    )
                )
            )

            session.execute(
                delete(TrainingSession)
                .where(
                    TrainingSession.id.in_(
                        regenerable_ids
                    )
                )
            )

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, session_id):

        session = SessionLocal()

        item = session.get(
            TrainingSession,
            session_id,
        )

        if item:

            session.delete(item)

            session.commit()

        session.close()