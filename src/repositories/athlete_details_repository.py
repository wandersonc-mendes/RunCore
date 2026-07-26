from database.database import SessionLocal
from models.athlete_details import AthleteDetails


class AthleteDetailsRepository:
    def get(self, athlete_id):
        session = SessionLocal(); item = session.get(AthleteDetails, athlete_id); session.close(); return item

    def save(self, athlete_id, personal, parq, training):
        session = SessionLocal()
        item = session.get(AthleteDetails, athlete_id) or AthleteDetails(athlete_id=athlete_id)
        item.personal = personal; item.parq = parq; item.training = training
        session.add(item); session.commit(); session.refresh(item); session.close(); return item
