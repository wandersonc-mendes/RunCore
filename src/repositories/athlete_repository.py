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

        session.close()

    def list_all(self):

        session = SessionLocal()

        athletes = (
            session.query(Athlete)
            .order_by(Athlete.name)
            .all()
        )

        session.close()

        return athletes