from sqlalchemy import func
from sqlalchemy import select

from database.database import SessionLocal
from models.athlete import Athlete


class AthleteRepository:

    def create(
        self,
        name: str,
        phone: str = "",
        email: str = "",
        goal: str = "",
        active: bool = True,
        notes: str = "",
        user_id: int | None = None,
        coach_user_id: int | None = None,
    ) -> Athlete:

        athlete = Athlete(
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip().lower(),
            goal=goal.strip(),
            active=active,
            notes=notes.strip(),
            user_id=user_id,
            coach_user_id=coach_user_id,
        )

        with SessionLocal() as session:

            session.add(athlete)
            session.commit()
            session.refresh(athlete)
            session.expunge(athlete)

        return athlete

    def create_for_user(
        self,
        user_id: int,
        coach_user_id: int,
        name: str,
        email: str,
    ) -> Athlete:

        existing = self.get_by_user_id(
            user_id,
        )

        if existing is not None:
            return existing

        return self.create(
            user_id=user_id,
            coach_user_id=coach_user_id,
            name=name,
            email=email,
            phone="",
            goal="",
            active=True,
            notes="Cadastro criado automaticamente após aprovação.",
        )

    def list_all(
        self,
    ) -> list[Athlete]:

        with SessionLocal() as session:

            statement = (
                select(Athlete)
                .order_by(Athlete.name)
            )

            athletes = list(
                session.scalars(statement)
            )

            for athlete in athletes:
                session.expunge(athlete)

            return athletes

    def list_by_coach(
        self,
        coach_user_id: int,
    ) -> list[Athlete]:

        with SessionLocal() as session:

            statement = (
                select(Athlete)
                .where(
                    Athlete.coach_user_id == coach_user_id,
                )
                .order_by(Athlete.name)
            )

            athletes = list(
                session.scalars(statement)
            )

            for athlete in athletes:
                session.expunge(athlete)

            return athletes

    def search(
        self,
        text: str,
    ) -> list[Athlete]:

        normalized_text = text.strip().lower()

        with SessionLocal() as session:

            statement = (
                select(Athlete)
                .where(
                    func.lower(Athlete.name).like(
                        f"%{normalized_text}%"
                    )
                )
                .order_by(Athlete.name)
            )

            athletes = list(
                session.scalars(statement)
            )

            for athlete in athletes:
                session.expunge(athlete)

            return athletes

    def search_by_coach(
        self,
        coach_user_id: int,
        text: str,
    ) -> list[Athlete]:

        normalized_text = text.strip().lower()

        with SessionLocal() as session:

            statement = (
                select(Athlete)
                .where(
                    Athlete.coach_user_id == coach_user_id,
                    func.lower(Athlete.name).like(
                        f"%{normalized_text}%"
                    ),
                )
                .order_by(Athlete.name)
            )

            athletes = list(
                session.scalars(statement)
            )

            for athlete in athletes:
                session.expunge(athlete)

            return athletes

    def get_by_id(
        self,
        athlete_id: int,
    ) -> Athlete | None:

        with SessionLocal() as session:

            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is not None:
                session.expunge(athlete)

            return athlete

    def get_by_user_id(
        self,
        user_id: int,
    ) -> Athlete | None:

        with SessionLocal() as session:

            statement = (
                select(Athlete)
                .where(
                    Athlete.user_id == user_id,
                )
            )

            athlete = session.scalar(
                statement,
            )

            if athlete is not None:
                session.expunge(athlete)

            return athlete

    def update(
        self,
        athlete_id: int,
        name: str,
        phone: str,
        email: str,
        goal: str,
        active: bool,
        notes: str,
    ) -> bool:

        with SessionLocal() as session:

            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return False

            athlete.name = name.strip()
            athlete.phone = phone.strip()
            athlete.email = email.strip().lower()
            athlete.goal = goal.strip()
            athlete.active = active
            athlete.notes = notes.strip()

            session.commit()

            return True

    def update_phone(
        self,
        athlete_id: int,
        phone: str,
    ) -> bool:

        with SessionLocal() as session:

            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return False

            athlete.phone = str(
                phone or "",
            ).strip()

            session.commit()

            return True

    def link_user_and_coach(
        self,
        athlete_id: int,
        user_id: int,
        coach_user_id: int,
    ) -> Athlete | None:

        with SessionLocal() as session:

            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return None

            athlete.user_id = user_id
            athlete.coach_user_id = coach_user_id

            session.commit()
            session.refresh(athlete)
            session.expunge(athlete)

            return athlete

    def delete(
        self,
        athlete_id: int,
    ) -> bool:

        with SessionLocal() as session:

            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return False

            session.delete(athlete)
            session.commit()

            return True