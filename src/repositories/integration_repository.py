from sqlalchemy import select

from database.database import SessionLocal
from models.external_integration import ExternalIntegration


class IntegrationRepository:

    def get(self, user_id, provider):
        session = SessionLocal()
        item = session.scalars(select(ExternalIntegration).where(ExternalIntegration.user_id == user_id, ExternalIntegration.provider == provider)).first()
        session.close()
        return item

    def get_by_id(self, integration_id):
        session = SessionLocal()
        item = session.get(
            ExternalIntegration,
            integration_id,
        )
        session.close()
        return item

    def get_by_external_user_id(
        self,
        provider,
        external_user_id,
    ):
        with SessionLocal() as session:
            item = session.scalars(
                select(ExternalIntegration).where(
                    ExternalIntegration.provider == provider,
                    ExternalIntegration.external_user_id
                    == str(external_user_id),
                )
            ).first()
            if item is not None:
                session.expunge(item)
            return item

    def save(self, item):
        session = SessionLocal()
        item = session.merge(item)
        session.commit()
        session.refresh(item)
        session.close()
        return item
