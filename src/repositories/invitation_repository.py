import secrets

from datetime import datetime

from sqlalchemy import select

from database.database import SessionLocal

from models.invitation import Invitation


class InvitationRepository:

    def create(
        self,
        coach_user_id: int,
        email: str = "",
    ) -> Invitation:

        with SessionLocal() as session:

            invitation = Invitation(
                coach_user_id=coach_user_id,
                email=email.strip().lower(),
                token=secrets.token_urlsafe(32),
                status="sent",
            )

            session.add(invitation)
            session.commit()
            session.refresh(invitation)
            session.expunge(invitation)

            return invitation

    def list_by_coach(
        self,
        coach_user_id: int,
    ) -> list[Invitation]:

        with SessionLocal() as session:

            statement = (
                select(Invitation)
                .where(
                    Invitation.coach_user_id == coach_user_id
                )
                .order_by(
                    Invitation.created_at.desc()
                )
            )

            invitations = list(
                session.scalars(statement)
            )

            for invitation in invitations:
                session.expunge(invitation)

            return invitations

    def get_by_id(
        self,
        invitation_id: int,
    ) -> Invitation | None:

        with SessionLocal() as session:

            invitation = session.get(
                Invitation,
                invitation_id,
            )

            if invitation is not None:
                session.expunge(invitation)

            return invitation

    def get_by_token(
        self,
        token: str,
    ) -> Invitation | None:

        with SessionLocal() as session:

            statement = (
                select(Invitation)
                .where(
                    Invitation.token == token
                )
            )

            invitation = session.scalar(
                statement,
            )

            if invitation is not None:
                session.expunge(invitation)

            return invitation

    def mark_pending(
        self,
        invitation_id: int,
        student_user_id: int,
        email: str,
    ) -> Invitation | None:

        with SessionLocal() as session:

            invitation = session.get(
                Invitation,
                invitation_id,
            )

            if invitation is None:
                return None

            invitation.student_user_id = student_user_id
            invitation.email = email.strip().lower()
            invitation.status = "pending"
            invitation.approved_at = None

            session.commit()
            session.refresh(invitation)
            session.expunge(invitation)

            return invitation

    def approve(
        self,
        invitation_id: int,
        student_user_id: int,
    ) -> Invitation | None:

        with SessionLocal() as session:

            invitation = session.get(
                Invitation,
                invitation_id,
            )

            if invitation is None:
                return None

            invitation.student_user_id = student_user_id
            invitation.status = "approved"
            invitation.approved_at = datetime.now()

            session.commit()
            session.refresh(invitation)
            session.expunge(invitation)

            return invitation