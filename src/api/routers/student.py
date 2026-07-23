from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import current_user
from api.routers.trainings import serialize_training
from repositories.access_repository import AccessRepository
from repositories.training_repository import TrainingRepository


router = APIRouter(prefix="/student", tags=["student"])
access = AccessRepository()
trainings = TrainingRepository()


@router.get("/training")
def get_student_training(user=Depends(current_user)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Este recurso é exclusivo da área do aluno.")

    athlete_id = access.athlete_for_student(user.id)
    if athlete_id is None:
        return None

    training = trainings.get_active_by_athlete(athlete_id)
    return serialize_training(training) if training else None
