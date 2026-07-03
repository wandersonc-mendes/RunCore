from sqlalchemy import func

from database.database import SessionLocal
from models.athlete import Athlete


class AthleteRepository:

    def create(
        self,
        name,
        phone,
        email,
        goal,
        active,
        notes,
    ):
        session = SessionLocal()

        athlete = Athlete(
            name=name,
            phone=phone,
            email=email,
            goal=goal,
            active=active,
            notes=notes,
        )

        session.add(athlete)
        session.commit()
        session.refresh(athlete)
        session.close()

        return athlete

    def list_all(self):

        session = SessionLocal()

        athletes = (
            session.query(Athlete)
            .order_by(Athlete.name)
            .all()
        )

        session.close()

        return athletes

    def search(self, text):

        session = SessionLocal()

        text = text.lower()

        athletes = (
            session.query(Athlete)
            .filter(
                func.lower(Athlete.name).like(f"%{text}%")
            )
            .order_by(Athlete.name)
            .all()
        )

        session.close()

        return athletes

    def get_by_id(self, athlete_id):

        session = SessionLocal()

        athlete = (
            session.query(Athlete)
            .filter(Athlete.id == athlete_id)
            .first()
        )

        session.close()

        return athlete

    def update(
        self,
        athlete_id,
        name,
        phone,
        email,
        goal,
        active,
        notes,
    ):

        session = SessionLocal()

        athlete = (
            session.query(Athlete)
            .filter(Athlete.id == athlete_id)
            .first()
        )

        if athlete is None:
            session.close()
            return False

        athlete.name = name
        athlete.phone = phone
        athlete.email = email
        athlete.goal = goal
        athlete.active = active
        athlete.notes = notes

        session.commit()
        session.close()

        return True

    def delete(self, athlete_id):

        session = SessionLocal()

        athlete = (
            session.query(Athlete)
            .filter(Athlete.id == athlete_id)
            .first()
        )

        if athlete is None:
            session.close()
            return False

        session.delete(athlete)
        session.commit()
        session.close()

        return True