from sqlalchemy.orm import joinedload

from core.physiology.ipt_service import IptService
from database.database import SessionLocal
from models.ipt_assessment import IptAssessment
from models.ipt_protocol import IptProtocol


class IptRepository:

    def ensure_default_protocols(self):

        session = SessionLocal()

        try:
            existing_codes = {
                code
                for (code,) in session.query(IptProtocol.code).all()
            }

            for definition in IptService.PROTOCOLS:
                if definition["code"] not in existing_codes:
                    session.add(
                        IptProtocol(
                            **definition,
                            active=True,
                        )
                    )

            session.commit()
        finally:
            session.close()

    def list_protocols(self):

        session = SessionLocal()

        try:
            return (
                session.query(IptProtocol)
                .filter(IptProtocol.active.is_(True))
                .order_by(IptProtocol.id)
                .all()
            )
        finally:
            session.close()

    def get_protocol(self, protocol_id):

        session = SessionLocal()

        try:
            return (
                session.query(IptProtocol)
                .filter(IptProtocol.id == protocol_id)
                .first()
            )
        finally:
            session.close()

    def create_assessment(
        self,
        athlete_id,
        protocol_id,
        short_result,
        long_result,
        result,
        notes,
    ):

        session = SessionLocal()

        try:
            assessment = IptAssessment(
                athlete_id=athlete_id,
                protocol_id=protocol_id,
                short_result=short_result,
                long_result=long_result,
                short_speed=result.short_speed,
                long_speed=result.long_speed,
                ipt_percentage=result.ipt_percentage,
                profile=result.profile,
                interpretation=result.interpretation,
                emphasis=result.emphasis,
                notes=notes,
            )

            session.add(assessment)
            session.commit()
            session.refresh(assessment)

            assessment = (
                session.query(IptAssessment)
                .options(joinedload(IptAssessment.protocol))
                .filter(IptAssessment.id == assessment.id)
                .first()
            )

            return self._serialize_assessment(assessment)
        finally:
            session.close()

    def list_by_athlete(self, athlete_id):

        session = SessionLocal()

        try:
            assessments = (
                session.query(IptAssessment)
                .options(joinedload(IptAssessment.protocol))
                .filter(IptAssessment.athlete_id == athlete_id)
                .order_by(IptAssessment.created_at.desc())
                .all()
            )

            return [
                self._serialize_assessment(item)
                for item in assessments
            ]
        finally:
            session.close()

    def delete(self, assessment_id):

        session = SessionLocal()

        try:
            assessment = (
                session.query(IptAssessment)
                .filter(IptAssessment.id == assessment_id)
                .first()
            )

            if assessment is None:
                return False

            session.delete(assessment)
            session.commit()

            return True
        finally:
            session.close()

    @staticmethod
    def _serialize_assessment(assessment):

        return {
            "id": assessment.id,
            "athlete_id": assessment.athlete_id,
            "protocol_id": assessment.protocol_id,
            "protocol_code": assessment.protocol.code,
            "protocol_name": assessment.protocol.name,
            "short_result": assessment.short_result,
            "long_result": assessment.long_result,
            "short_speed": assessment.short_speed,
            "long_speed": assessment.long_speed,
            "ipt_percentage": assessment.ipt_percentage,
            "profile": assessment.profile,
            "interpretation": assessment.interpretation,
            "emphasis": assessment.emphasis,
            "notes": assessment.notes,
            "created_at": assessment.created_at,
        }