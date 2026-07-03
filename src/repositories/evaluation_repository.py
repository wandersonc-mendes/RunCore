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
        vo2,
    ):
        session = SessionLocal()

        evaluation = Evaluation(
            athlete_id=athlete_id,
            weight=weight,
            height=height,
            max_hr=max_hr,
            resting_hr=resting_hr,
            vo2=vo2,
        )

        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)
        session.close()

        return evaluation

    def list_by_athlete(self, athlete_id):

        session = SessionLocal()

        evaluations = (
            session.query(Evaluation)
            .filter(
                Evaluation.athlete_id == athlete_id
            )
            .order_by(
                Evaluation.created_at.desc()
            )
            .all()
        )

        session.close()

        return evaluations

    def last_evaluation(self, athlete_id):

        session = SessionLocal()

        evaluation = (
            session.query(Evaluation)
            .filter(
                Evaluation.athlete_id == athlete_id
            )
            .order_by(
                Evaluation.created_at.desc()
            )
            .first()
        )

        session.close()

        return evaluation

    def delete(self, evaluation_id):

        session = SessionLocal()

        evaluation = (
            session.query(Evaluation)
            .filter(
                Evaluation.id == evaluation_id
            )
            .first()
        )

        if evaluation is None:
            session.close()
            return False

        session.delete(evaluation)
        session.commit()
        session.close()

        return True