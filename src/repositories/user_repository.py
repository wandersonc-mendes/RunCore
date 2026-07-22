from sqlalchemy import func
from sqlalchemy import select

from database.database import SessionLocal
from models.user import User


class UserRepository:

    def get_by_id(self, user_id: int) -> User | None:

        with SessionLocal() as session:

            statement = select(User).where(
                User.id == user_id,
            )

            return session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:

        normalized_email = email.strip().lower()

        with SessionLocal() as session:

            statement = select(User).where(
                func.lower(User.email) == normalized_email,
            )

            return session.scalar(statement)

    def email_exists(self, email: str) -> bool:

        return self.get_by_email(email) is not None

    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> User:

        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
        )

        with SessionLocal() as session:

            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)

        return user