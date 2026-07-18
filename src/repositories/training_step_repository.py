from sqlalchemy import select

from database.database import SessionLocal
from models.training_step import (
    TrainingStep,
)


class TrainingStepRepository:

    def create(self, step):

        session = SessionLocal()

        session.add(step)

        session.commit()

        session.refresh(step)

        session.close()

        return step

    def create_many(self, steps):

        session = SessionLocal()

        session.add_all(steps)

        session.commit()

        session.close()

    def update(self, step):

        session = SessionLocal()

        step = session.merge(step)

        session.commit()

        session.refresh(step)

        session.close()

        return step

    def list_by_session(
        self,
        session_id,
    ):

        session = SessionLocal()

        items = session.scalars(
            select(TrainingStep)
            .where(
                TrainingStep.session_id == session_id
            )
            .order_by(
                TrainingStep.order
            )
        ).all()

        session.close()

        return items

    def delete_by_session(
        self,
        session_id,
    ):

        session = SessionLocal()

        items = session.scalars(
            select(TrainingStep)
            .where(
                TrainingStep.session_id == session_id
            )
        ).all()

        for item in items:
            session.delete(item)

        session.commit()

        session.close()