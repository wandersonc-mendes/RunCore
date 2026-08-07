from sqlalchemy import select

from database.database import SessionLocal
from models.athlete import Athlete
from models.athlete_profile import AthleteProfile
from models.external_integration import ExternalIntegration
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

    def list_for_athlete(self, athlete_id):
        if athlete_id is None:
            return []

        with SessionLocal() as session:
            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return []

            user_id = athlete.user_id

            if user_id is None:
                user_id = session.scalar(
                    select(AthleteProfile.user_id)
                    .where(
                        AthleteProfile.athlete_id
                        == athlete_id,
                    )
                )

            if user_id is None:
                return []

            items = session.scalars(
                select(ImportedActivity)
                .join(
                    ExternalIntegration,
                    ExternalIntegration.id
                    == ImportedActivity.integration_id,
                )
                .where(
                    ExternalIntegration.user_id
                    == user_id,
                )
                .order_by(
                    ImportedActivity.start_at.asc(),
                    ImportedActivity.id.asc(),
                )
            ).all()

            for item in items:
                session.expunge(item)

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
