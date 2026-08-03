from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import current_user
from models.goal import Goal
from repositories.athlete_repository import AthleteRepository
from repositories.goal_repository import GoalRepository
from repositories.training_repository import TrainingRepository


router = APIRouter(prefix="/goals", tags=["goals"])
athletes = AthleteRepository()
goals = GoalRepository()
trainings = TrainingRepository()


class GoalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    distance: float = Field(gt=0)
    target_date: date
    priority: str = "Principal"


@router.get("")
def list_goals(user=Depends(current_user)):
    return goals.list_for_user(user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, user=Depends(current_user)):
    return goals.create(Goal(user_id=user.id, **payload.model_dump()))


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_goal(
    goal_id: int,
    user=Depends(current_user),
):
    goal = goals.get_for_user(
        goal_id,
        user.id,
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Meta não encontrada.",
        )

    athlete = athletes.get_by_user_id(
        user.id,
    )

    active_training = (
        trainings.get_active_by_athlete(
            athlete.id,
        )
        if athlete is not None
        else None
    )

    goal_is_used_by_training = (
        active_training is not None
        and (
            active_training.target_date
            == goal.target_date
            or (
                str(
                    active_training.objective
                    or "",
                ).strip().lower()
                == str(
                    goal.name
                    or "",
                ).strip().lower()
            )
        )
    )

    if goal_is_used_by_training:
        raise HTTPException(
            status_code=409,
            detail=(
                "Esta meta está vinculada ao planejamento ativo. "
                "Finalize ou desative o planejamento antes "
                "de excluir a meta."
            ),
        )

    if not goals.delete_for_user(
        goal_id,
        user.id,
    ):
        raise HTTPException(
            status_code=404,
            detail="Meta não encontrada.",
        )
