from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import current_user
from models.goal import Goal
from repositories.goal_repository import GoalRepository


router = APIRouter(prefix="/goals", tags=["goals"])
goals = GoalRepository()


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


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, user=Depends(current_user)):
    if not goals.delete_for_user(goal_id, user.id):
        raise HTTPException(status_code=404, detail="Meta não encontrada.")
