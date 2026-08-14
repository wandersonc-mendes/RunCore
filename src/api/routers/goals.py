from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.access_control import require_athlete_access
from api.dependencies import current_user, require_coach
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


def managed_athlete(
    athlete_id: int,
    coach,
):
    athlete = require_athlete_access(
        athlete_id,
        coach,
    )

    if athlete.user_id is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "O atleta ainda não possui uma conta "
                "de usuário vinculada."
            ),
        )

    return athlete


def goal_used_by_active_training(
    athlete_id: int,
    goal,
) -> bool:
    active_training = (
        trainings.get_active_by_athlete(
            athlete_id,
        )
    )

    return (
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


@router.get("/athletes/{athlete_id}")
def list_athlete_goals(
    athlete_id: int,
    coach=Depends(require_coach),
):
    athlete = managed_athlete(
        athlete_id,
        coach,
    )

    return goals.list_for_user(
        athlete.user_id,
    )


@router.post(
    "/athletes/{athlete_id}",
    status_code=status.HTTP_201_CREATED,
)
def create_athlete_goal(
    athlete_id: int,
    payload: GoalCreate,
    coach=Depends(require_coach),
):
    athlete = managed_athlete(
        athlete_id,
        coach,
    )

    return goals.create(
        Goal(
            user_id=athlete.user_id,
            **payload.model_dump(),
        )
    )


@router.delete(
    "/athletes/{athlete_id}/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_athlete_goal(
    athlete_id: int,
    goal_id: int,
    coach=Depends(require_coach),
):
    athlete = managed_athlete(
        athlete_id,
        coach,
    )

    goal = goals.get_for_user(
        goal_id,
        athlete.user_id,
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Meta não encontrada.",
        )

    if goal_used_by_active_training(
        athlete.id,
        goal,
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Esta meta está vinculada ao "
                "planejamento ativo. Finalize ou "
                "desative o planejamento antes "
                "de excluir a meta."
            ),
        )

    if not goals.delete_for_user(
        goal_id,
        athlete.user_id,
    ):
        raise HTTPException(
            status_code=404,
            detail="Meta não encontrada.",
        )


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

    goal_is_used_by_training = (
        athlete is not None
        and goal_used_by_active_training(
            athlete.id,
            goal,
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
