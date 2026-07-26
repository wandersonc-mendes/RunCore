from sqlalchemy import select

from database.database import SessionLocal
from models.goal import Goal


class GoalRepository:
    def list_for_user(self, user_id):
        session = SessionLocal()
        items = session.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.target_date)).all()
        session.close()
        return items

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
