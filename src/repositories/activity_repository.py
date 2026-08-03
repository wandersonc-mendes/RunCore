from sqlalchemy import select

from database.database import SessionLocal
from models.imported_activity import ImportedActivity
from models.training import Training
from models.training_session import TrainingSession


class ActivityRepository:

    def get_by_provider_id(self, provider_activity_id):
        session = SessionLocal()
        item = session.scalars(select(ImportedActivity).where(ImportedActivity.provider_activity_id == str(provider_activity_id))).first()
        session.close()
        return item

    def save(self, item):
        session = SessionLocal()
        item = session.merge(item)
        session.commit()
        session.refresh(item)
        session.close()
        return item

    def link_training_session(
        self,
        activity_id,
        athlete_id,
        activity_day,
    ):
        if (
            activity_id is None
            or athlete_id is None
            or activity_day is None
        ):
            return None

        with SessionLocal() as session:
            activity = session.get(
                ImportedActivity,
                activity_id,
            )

            if (
                activity is None
                or activity.training_session_id is not None
            ):
                return activity

            linked_session_ids = select(
                ImportedActivity.training_session_id
            ).where(
                ImportedActivity.training_session_id.is_not(
                    None,
                )
            )

            candidates = session.scalars(
                select(TrainingSession)
                .join(
                    Training,
                    Training.id
                    == TrainingSession.training_id,
                )
                .where(
                    Training.athlete_id == athlete_id,
                    TrainingSession.scheduled_date
                    == activity_day,
                    TrainingSession.id.not_in(
                        linked_session_ids,
                    ),
                )
                .order_by(TrainingSession.id)
            ).all()

            if len(candidates) != 1:
                return activity

            activity.training_session_id = (
                candidates[0].id
            )
            session.commit()
            session.refresh(activity)
            session.expunge(activity)
            return activity

    def list_for_integration(self, integration_id):
        session = SessionLocal()
        items = session.scalars(select(ImportedActivity).where(ImportedActivity.integration_id == integration_id).order_by(ImportedActivity.start_at.desc()).limit(20)).all()
        session.close()
        return items

    def get_for_integration(self, activity_id, integration_id):
        session = SessionLocal()
        item = session.scalars(
            select(ImportedActivity).where(
                ImportedActivity.id == activity_id,
                ImportedActivity.integration_id == integration_id,
            )
        ).first()
        session.close()
        return item
