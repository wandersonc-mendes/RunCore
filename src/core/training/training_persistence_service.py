from datetime import date, timedelta

from core.training.training_cycle_builder import (
    TrainingCycleBuilder,
)
from models.training import Training
from repositories.training_repository import (
    TrainingRepository,
)
from repositories.training_session_repository import (
    TrainingSessionRepository,
)
from core.training.training_step_service import (
    TrainingStepService,
)


class TrainingPersistenceService:

    def __init__(self):

        self.training_repository = (
            TrainingRepository()
        )

        self.session_repository = (
            TrainingSessionRepository()
        )

        self.step_service = (
            TrainingStepService()
        )

    def create_training(
        self,
        athlete_id: int,
        vdot: float | None,
        name: str,
        methodology: str,
        objective: str,
        target_distance: float,
        start_date: date | None = None,
        target_date: date | None = None,
        total_weeks: int = 8,
        ipt_profile: str | None = None,
        training_days: list[int] | None = None,
    ):

        training = Training()

        training.athlete_id = athlete_id
        training.name = name
        training.methodology = methodology
        training.objective = objective
        training.target_distance = target_distance
        training.start_date = start_date or date.today()
        training.target_date = target_date

        training = self.training_repository.create(
            training
        )

        self._generate_sessions(
            training.id,
            vdot,
            total_weeks,
            ipt_profile,
            target_distance=target_distance,
            training_days=training_days,
            start_date=training.start_date,
        )

        return training

    def regenerate_training(
        self,
        training_id: int,
        vdot: float | None,
        ipt_profile: str | None = None,
        total_weeks: int | None = None,
        training_days: list[int] | None = None,
    ):

        sessions = (
            self.session_repository.list_by_training(
                training_id
            )
        )

        preserved_dates = {
            training_session.scheduled_date
            for training_session in sessions
            if (
                training_session.scheduled_date
                is not None
                and (
                    training_session.manual_override
                    or training_session.completed
                    or (
                        training_session.scheduled_date
                        < date.today()
                    )
                )
            )
        }

        current_total_weeks = max(
            (
                session.week
                for session in sessions
            ),
            default=8,
        )

        total_weeks = total_weeks or current_total_weeks

        training = self.training_repository.get_by_id(
            training_id
        )

        if training is None:
            raise ValueError(
                "Planejamento não encontrado."
            )

        if training.start_date is None:
            training.start_date = date.today()
            training = self.training_repository.update(
                training
            )

        target_distance = training.target_distance

        self.session_repository.delete_regenerable_by_training(
            training_id,
            date.today(),
        )

        self._generate_sessions(
            training_id,
            vdot,
            total_weeks,
            ipt_profile,
            target_distance=target_distance,
            training_days=training_days,
            start_date=training.start_date,
            excluded_dates=preserved_dates,
        )

    def _generate_sessions(
        self,
        training_id: int,
        vdot: float | None,
        total_weeks: int,
        ipt_profile: str | None = None,
        target_distance: float | None = None,
        training_days: list[int] | None = None,
        start_date: date | None = None,
        excluded_dates: set[date] | None = None,
    ):

        if vdot is None:
            cycle = TrainingCycleBuilder.initial(
                total_weeks=total_weeks,
                target_distance=target_distance,
                training_days=training_days,
            )
        else:
            cycle = TrainingCycleBuilder.base(
                vdot,
                total_weeks,
                ipt_profile=ipt_profile,
                target_distance=target_distance,
            )

        sessions = (
            TrainingCycleBuilder.to_training_sessions(
                training_id,
                cycle,
            )
        )

        if start_date is not None:
            cycle_week_monday = (
                start_date
                - timedelta(
                    days=start_date.weekday()
                )
            )

            scheduled_sessions = []

            for training_session in sessions:
                scheduled_date = (
                    cycle_week_monday
                    + timedelta(
                        weeks=max(
                            training_session.week - 1,
                            0,
                        ),
                        days=training_session.weekday,
                    )
                )

                if scheduled_date < start_date:
                    continue

                if (
                    excluded_dates
                    and scheduled_date
                    in excluded_dates
                ):
                    continue

                training_session.scheduled_date = (
                    scheduled_date
                )
                scheduled_sessions.append(
                    training_session
                )

            sessions = scheduled_sessions

        self.session_repository.create_many(
            sessions
        )

        for training_session in sessions:
            repetitions = int(
                training_session.repetitions or 0
            )

            distance_unit = (
                "m"
                if repetitions > 0
                else "km"
            )

            rpe_by_zone = {
                "Easy": (2, 4),
                "Marathon": (4, 6),
                "Threshold": (6, 8),
                "Interval": (8, 9),
                "Repetition": (9, 10),
            }

            rpe_min, rpe_max = rpe_by_zone.get(
                str(training_session.zone),
                (3, 5),
            )

            recovery = (
                (
                    f"{training_session.recovery} m"
                    if repetitions > 0
                    else str(training_session.recovery)
                )
                if training_session.recovery
                else ""
            )

            step_distance = getattr(
                training_session,
                "_generated_step_distance",
                training_session.planned_distance or 0,
            )

            self.step_service.save(
                training_session.id,
                [
                    {
                        "type": "Parte principal",
                        "prescription_type": "distance",
                        "intensity_type": "rpe",
                        "distance": step_distance,
                        "distance_unit": distance_unit,
                        "duration": 0,
                        "repetitions": repetitions,
                        "recovery": recovery,
                        "pace_min": "",
                        "pace_max": "",
                        "heart_rate_min": None,
                        "heart_rate_max": None,
                        "rpe_min": rpe_min,
                        "rpe_max": rpe_max,
                        "notes": "",
                    }
                ],
            )

    def delete_training(
        self,
        training_id: int,
    ):

        self.training_repository.delete(
            training_id
        )