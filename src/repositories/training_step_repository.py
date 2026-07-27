from sqlalchemy import delete, select, text

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

    def list_by_sessions(
        self,
        session_ids,
    ):
        if not session_ids:
            return {}

        session = SessionLocal()

        try:
            items = session.scalars(
                select(TrainingStep)
                .where(
                    TrainingStep.session_id.in_(session_ids)
                )
                .order_by(
                    TrainingStep.session_id,
                    TrainingStep.order,
                )
            ).all()

            grouped = {
                session_id: []
                for session_id in session_ids
            }

            for item in items:
                grouped.setdefault(
                    item.session_id,
                    [],
                ).append(item)

            return grouped
        finally:
            session.close()

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

    def replace_by_session(self, session_id, steps):

        session = SessionLocal()

        try:
            if session.bind.dialect.name == "postgresql":
                session.execute(
                    text(
                        "SET LOCAL lock_timeout = '5s'"
                    )
                )
                session.execute(
                    text(
                        "SET LOCAL statement_timeout = '15s'"
                    )
                )

            session.execute(
                delete(TrainingStep).where(
                    TrainingStep.session_id == session_id
                )
            )

            session.add_all(
                steps
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
