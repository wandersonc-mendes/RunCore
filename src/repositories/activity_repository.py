from sqlalchemy import select

from database.database import SessionLocal
from models.imported_activity import ImportedActivity


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
