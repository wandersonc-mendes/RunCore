from sqlalchemy import select

from database.database import SessionLocal
from models.athlete import Athlete
from models.athlete_profile import AthleteProfile
from models.coach_athlete import CoachAthlete


class AccessRepository:

    def link_coach_to_athlete(self, coach_id, athlete_id):
        session = SessionLocal()
        if session.get(CoachAthlete, (coach_id, athlete_id)) is None:
            session.add(CoachAthlete(coach_id=coach_id, athlete_id=athlete_id))
            session.commit()
        session.close()

    def link_student_to_athlete(self, user_id, athlete_id):
        session = SessionLocal()
        session.add(AthleteProfile(user_id=user_id, athlete_id=athlete_id))
        session.commit()
        session.close()

    def athlete_for_student(self, user_id):
        with SessionLocal() as session:
            athlete_id = session.scalar(
                select(Athlete.id).where(
                    Athlete.user_id == user_id,
                )
            )

            if athlete_id is not None:
                return athlete_id

            profile = session.get(
                AthleteProfile,
                user_id,
            )

            return (
                profile.athlete_id
                if profile is not None
                else None
            )

    def coach_has_athlete(self, coach_id, athlete_id):
        session = SessionLocal()
        link = session.get(CoachAthlete, (coach_id, athlete_id))
        session.close()
        return link is not None

    def athletes_for_coach(self, coach_id):
        session = SessionLocal()
        athletes = session.scalars(select(Athlete).join(CoachAthlete).where(CoachAthlete.coach_id == coach_id).order_by(Athlete.name)).all()
        session.close()
        return athletes

    def assign_unlinked_athletes(self, coach_id):
        session = SessionLocal()
        athlete_ids = session.scalars(select(Athlete.id).outerjoin(CoachAthlete).where(CoachAthlete.athlete_id.is_(None))).all()
        session.add_all([CoachAthlete(coach_id=coach_id, athlete_id=athlete_id) for athlete_id in athlete_ids])
        session.commit()
        session.close()
