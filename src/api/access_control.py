from fastapi import HTTPException

from repositories.access_repository import AccessRepository
from repositories.athlete_repository import AthleteRepository


athletes = AthleteRepository()
access = AccessRepository()


def coach_can_access_athlete(coach, athlete) -> bool:
    if coach.role == "master":
        return True

    if getattr(athlete, "coach_user_id", None) == coach.id:
        return True

    return access.coach_has_athlete(
        coach.id,
        athlete.id,
    )


def require_athlete_access(
    athlete_id: int,
    coach,
):
    athlete = athletes.get_by_id(athlete_id)

    if athlete is None:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado.",
        )

    if not coach_can_access_athlete(
        coach,
        athlete,
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não possui acesso a este atleta.",
        )

    return athlete
