from sqlalchemy import select

from database.database import SessionLocal
from models.activity_feedback import ActivityFeedback


class ActivityFeedbackRepository:
    def get_for_activity(self, activity_id):
        session = SessionLocal()
        item = session.scalars(select(ActivityFeedback).where(ActivityFeedback.activity_id == activity_id)).first()
        session.close()
        return item

    def save(self, activity_id, athlete_id, payload):
        session = SessionLocal()
        item = session.scalars(select(ActivityFeedback).where(ActivityFeedback.activity_id == activity_id)).first()
        if item is None:
            item = ActivityFeedback(activity_id=activity_id, athlete_id=athlete_id)
            session.add(item)
        item.perceived_effort = payload.perceived_effort
        item.feeling = payload.feeling
        item.pain = payload.pain
        item.sleep_quality = payload.sleep_quality
        item.pre_fatigue = payload.pre_fatigue
        item.notes = payload.notes
        session.commit()
        session.refresh(item)
        session.expunge(item)
        session.close()
        return item
