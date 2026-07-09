from sqlalchemy import select

from database.database import SessionLocal
from models.training import Training


class TrainingRepository:

    def create(self, training):

        session = SessionLocal()

        session.add(training)

        session.commit()

        session.refresh(training)

        session.close()

        return training

    def update(self, training):

        session = SessionLocal()

        training = session.merge(training)

        session.commit()

        session.refresh(training)

        session.close()

        return training

    def delete(self, training_id):

        session = SessionLocal()

        training = session.get(
            Training,
            training_id,
        )

        if training:

            session.delete(training)

            session.commit()

        session.close()

    def get_by_id(self, training_id):

        session = SessionLocal()

        training = session.get(
            Training,
            training_id,
        )

        session.close()

        return training

    def list_by_athlete(
        self,
        athlete_id,
    ):

        session = SessionLocal()

        trainings = session.scalars(
            select(Training)
            .where(
                Training.athlete_id == athlete_id
            )
            .order_by(
                Training.start_date.desc()
            )
        ).all()

        session.close()

        return trainings