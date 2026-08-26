from sqlalchemy import func
from sqlalchemy import select

from database.database import SessionLocal
from models.coach_profile import CoachProfile
from models.user import User


class UserRepository:

    def create_coach_with_profile(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        is_active: bool,
        profile: dict,
    ) -> User:

        with SessionLocal() as session:

            user = User(
                name=name.strip(),
                email=email.strip().lower(),
                password_hash=password_hash,
                role="coach",
                is_active=is_active,
            )

            session.add(user)
            session.flush()

            session.add(
                CoachProfile(
                    user_id=user.id,
                    **profile,
                )
            )

            session.commit()
            session.refresh(user)
            session.expunge(user)

            return user

    def list_all(self) -> list[User]:

        with SessionLocal() as session:

            users = session.scalars(
                select(User)
                .where(
                    User.email.not_like("__removed__%"),
                )
                .order_by(User.name, User.id),
            ).all()

            for user in users:
                session.expunge(user)

            return list(users)


    def count_active_by_role(
        self,
        role: str,
    ) -> int:

        with SessionLocal() as session:

            statement = select(func.count(User.id)).where(
                User.role == role,
                User.is_active.is_(True),
            )

            return int(session.scalar(statement) or 0)

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        with SessionLocal() as session:

            statement = select(User).where(
                User.id == user_id,
            )

            return session.scalar(statement)

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        normalized_email = email.strip().lower()

        with SessionLocal() as session:

            statement = select(User).where(
                func.lower(User.email) == normalized_email,
            )

            return session.scalar(statement)

    def email_exists(
        self,
        email: str,
    ) -> bool:

        return self.get_by_email(email) is not None

    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str,
        is_active: bool = True,
    ) -> User:

        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )

        with SessionLocal() as session:

            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)

        return user

    def activate(
        self,
        user_id: int,
    ) -> User | None:

        with SessionLocal() as session:

            user = session.get(
                User,
                user_id,
            )

            if user is None:
                return None

            user.is_active = True

            session.commit()
            session.refresh(user)
            session.expunge(user)

        return user

    def update_access(
        self,
        user_id: int,
        *,
        name: str,
        role: str,
        is_active: bool,
    ) -> User | None:

        with SessionLocal() as session:

            user = session.get(User, user_id)

            if user is None:
                return None

            user.name = name.strip()
            user.role = role
            user.is_active = is_active

            session.commit()
            session.refresh(user)
            session.expunge(user)

            return user

    def delete(
        self,
        user_id: int,
    ) -> bool:

        with SessionLocal() as session:

            user = session.get(
                User,
                user_id,
            )

            if user is None:
                return False

            session.delete(user)
            session.commit()

            return True


    def update_password(
        self,
        user_id: int,
        password_hash: str,
    ) -> User | None:

        with SessionLocal() as session:

            user = session.get(
                User,
                user_id,
            )

            if user is None:
                return None

            user.password_hash = password_hash

            session.commit()
            session.refresh(user)
            session.expunge(user)

            return user
