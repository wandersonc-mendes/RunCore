from database.database import SessionLocal
from models.evaluation import Evaluation


class EvaluationRepository:

    def create(
        self,
        athlete_id,
        weight,
        height,
        max_hr,
        resting_hr,
        test_type,
        distance,
        time_seconds,
        vdot,
        test_date=None,
    ):
        session = SessionLocal()

        try:
            evaluation = Evaluation(
                athlete_id=athlete_id,
                weight=weight,
                height=height,
                max_hr=max_hr,
                resting_hr=resting_hr,
                test_type=test_type,
                distance=distance,
                time_seconds=time_seconds,
                vdot=vdot,
                test_date=test_date,
            )

            session.add(evaluation)
            session.commit()
            session.refresh(evaluation)

            return evaluation

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def update(self, evaluation):
        session = SessionLocal()

        try:
            evaluation = session.merge(evaluation)

            session.commit()
            session.refresh(evaluation)

            return evaluation

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def get_by_id(self, evaluation_id):
        session = SessionLocal()

        try:
            return (
                session.query(Evaluation)
                .filter(Evaluation.id == evaluation_id)
                .first()
            )

        finally:
            session.close()

    def list_by_athlete(self, athlete_id):
        session = SessionLocal()

        try:
            return (
                session.query(Evaluation)
                .filter(Evaluation.athlete_id == athlete_id)
                .order_by(Evaluation.created_at.desc())
                .all()
            )

        finally:
            session.close()

    def last_evaluation(self, athlete_id):
        session = SessionLocal()

        try:
            return (
                session.query(Evaluation)
                .filter(Evaluation.athlete_id == athlete_id)
                .order_by(Evaluation.created_at.desc())
                .first()
            )

        finally:
            session.close()

    def delete(self, evaluation_id):
        session = SessionLocal()

        try:
            evaluation = (
                session.query(Evaluation)
                .filter(Evaluation.id == evaluation_id)
                .first()
            )

            if evaluation is None:
                return False

            session.delete(evaluation)
            session.commit()

            return True

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()