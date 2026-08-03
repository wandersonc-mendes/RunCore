from datetime import date

from sqlalchemy import select

from database.database import SessionLocal
from models.goal import Goal


class GoalRepository:
    def list_for_user(self, user_id):
        session = SessionLocal()
        items = session.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.target_date)).all()
        session.close()
        return items

    def get_for_user(
        self,
        goal_id,
        user_id,
    ):
        with SessionLocal() as session:
            goal = session.scalar(
                select(Goal).where(
                    Goal.id == goal_id,
                    Goal.user_id == user_id,
                )
            )

            if goal is not None:
                session.expunge(goal)

            return goal

    def get_active_primary_for_user(
        self,
        user_id,
    ):
        with SessionLocal() as session:
            statement = (
                select(Goal)
                .where(
                    Goal.user_id == user_id,
                    Goal.target_date >= date.today(),
                    Goal.status == "Em andamento",
                )
                .order_by(
                    Goal.target_date.asc(),
                )
            )

            items = list(
                session.scalars(statement)
            )

            principal = next(
                (
                    item
                    for item in items
                    if str(
                        item.priority or "",
                    ).strip().lower()
                    == "principal"
                ),
                None,
            )

            selected = (
                principal
                or (items[0] if items else None)
            )

            if selected is not None:
                session.expunge(selected)

            return selected

    def create(self, goal):
        session = SessionLocal()
        session.add(goal)
        session.commit()
        session.refresh(goal)
        session.close()
        return goal

    def delete_for_user(self, goal_id, user_id):
        session = SessionLocal()
        goal = session.scalars(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)).first()
        if goal:
            session.delete(goal)
            session.commit()
        session.close()
        return goal is not None
