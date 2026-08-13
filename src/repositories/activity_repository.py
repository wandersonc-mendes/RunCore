from datetime import datetime

from sqlalchemy import select

from database.database import SessionLocal
from models.athlete import Athlete
from models.athlete_profile import AthleteProfile
from models.external_integration import ExternalIntegration
from models.imported_activity import ImportedActivity
from models.training import Training
from models.training_session import TrainingSession


class ActivityRepository:

    def sync_strava_batch(
        self,
        integration_id,
        strava_activities,
        athlete_id=None,
    ):
        provider_ids = [
            str(item["id"])
            for item in strava_activities
            if item.get("id") is not None
        ]

        if not provider_ids:
            return 0

        with SessionLocal() as session:
            existing_items = session.scalars(
                select(ImportedActivity)
                .where(
                    ImportedActivity.provider_activity_id.in_(
                        provider_ids
                    )
                )
            ).all()

            existing_by_provider = {
                item.provider_activity_id: item
                for item in existing_items
            }

            local_days = set()

            for activity in strava_activities:
                sport_type = str(
                    activity.get("sport_type")
                    or activity.get("type")
                    or ""
                ).lower()

                if sport_type not in {
                    "run",
                    "virtualrun",
                    "trailrun",
                }:
                    continue

                local_start = activity.get(
                    "start_date_local",
                )

                if not local_start:
                    continue

                local_days.add(
                    datetime.fromisoformat(
                        local_start.replace(
                            "Z",
                            "+00:00",
                        )
                    ).date()
                )

            sessions_by_day = {}

            if athlete_id is not None and local_days:
                candidates = session.scalars(
                    select(TrainingSession)
                    .join(
                        Training,
                        Training.id
                        == TrainingSession.training_id,
                    )
                    .where(
                        Training.athlete_id == athlete_id,
                        TrainingSession.scheduled_date.in_(
                            local_days
                        ),
                    )
                    .order_by(
                        TrainingSession.scheduled_date,
                        TrainingSession.id,
                    )
                ).all()

                for candidate in candidates:
                    sessions_by_day.setdefault(
                        candidate.scheduled_date,
                        [],
                    ).append(candidate)

            linked_session_ids = set(
                session.scalars(
                    select(
                        ImportedActivity.training_session_id
                    )
                    .where(
                        ImportedActivity.training_session_id
                        .is_not(None)
                    )
                ).all()
            )

            imported = 0

            for activity in strava_activities:
                provider_id = str(activity["id"])
                item = existing_by_provider.get(
                    provider_id
                )

                if item is None:
                    item = ImportedActivity(
                        integration_id=integration_id,
                        provider_activity_id=provider_id,
                    )
                    session.add(item)
                    existing_by_provider[
                        provider_id
                    ] = item
                    imported += 1

                item.integration_id = integration_id
                item.name = activity.get(
                    "name",
                    "Atividade",
                )
                item.sport_type = (
                    activity.get("sport_type")
                    or activity.get("type", "")
                )
                item.distance = round(
                    activity.get("distance", 0)
                    / 1000,
                    3,
                )
                item.moving_time = activity.get(
                    "moving_time",
                    0,
                )
                item.elapsed_time = activity.get(
                    "elapsed_time"
                )
                item.average_speed = activity.get(
                    "average_speed"
                )
                item.max_speed = activity.get(
                    "max_speed"
                )
                item.average_heartrate = activity.get(
                    "average_heartrate"
                )
                item.max_heartrate = activity.get(
                    "max_heartrate"
                )
                item.average_cadence = activity.get(
                    "average_cadence"
                )
                item.total_elevation_gain = activity.get(
                    "total_elevation_gain"
                )

                start_date = activity.get(
                    "start_date"
                )
                item.start_at = (
                    datetime.fromisoformat(
                        start_date.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                    if start_date
                    else None
                )

                if (
                    item.training_session_id
                    is not None
                ):
                    continue

                sport_type = str(
                    activity.get("sport_type")
                    or activity.get("type")
                    or ""
                ).lower()

                if sport_type not in {
                    "run",
                    "virtualrun",
                    "trailrun",
                }:
                    continue

                local_start = activity.get(
                    "start_date_local"
                )

                if (
                    athlete_id is None
                    or not local_start
                ):
                    continue

                local_day = datetime.fromisoformat(
                    local_start.replace(
                        "Z",
                        "+00:00",
                    )
                ).date()

                available = [
                    candidate
                    for candidate in sessions_by_day.get(
                        local_day,
                        [],
                    )
                    if candidate.id
                    not in linked_session_ids
                ]

                if len(available) != 1:
                    continue

                item.training_session_id = (
                    available[0].id
                )
                linked_session_ids.add(
                    available[0].id
                )

            session.flush()
            session.commit()

            return imported


    def get_by_provider_id(self, provider_activity_id):
        session = SessionLocal()
        item = session.scalars(select(ImportedActivity).where(ImportedActivity.provider_activity_id == str(provider_activity_id))).first()
        session.close()
        return item

    def save(self, item):
        session = SessionLocal()
        item = session.merge(item)
        session.commit()
        session.refresh(item)
        session.close()
        return item

    def link_training_session(
        self,
        activity_id,
        athlete_id,
        activity_day,
    ):
        if (
            activity_id is None
            or athlete_id is None
            or activity_day is None
        ):
            return None

        with SessionLocal() as session:
            activity = session.get(
                ImportedActivity,
                activity_id,
            )

            if (
                activity is None
                or activity.training_session_id is not None
            ):
                return activity

            linked_session_ids = select(
                ImportedActivity.training_session_id
            ).where(
                ImportedActivity.training_session_id.is_not(
                    None,
                )
            )

            candidates = session.scalars(
                select(TrainingSession)
                .join(
                    Training,
                    Training.id
                    == TrainingSession.training_id,
                )
                .where(
                    Training.athlete_id == athlete_id,
                    TrainingSession.scheduled_date
                    == activity_day,
                    TrainingSession.id.not_in(
                        linked_session_ids,
                    ),
                )
                .order_by(TrainingSession.id)
            ).all()

            if len(candidates) != 1:
                return activity

            activity.training_session_id = (
                candidates[0].id
            )
            session.commit()
            session.refresh(activity)
            session.expunge(activity)
            return activity

    def list_for_integration(self, integration_id):
        session = SessionLocal()
        items = session.scalars(select(ImportedActivity).where(ImportedActivity.integration_id == integration_id).order_by(ImportedActivity.start_at.desc()).limit(20)).all()
        session.close()
        return items

    def list_for_athlete(self, athlete_id):
        if athlete_id is None:
            return []

        with SessionLocal() as session:
            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return []

            user_id = athlete.user_id

            if user_id is None:
                user_id = session.scalar(
                    select(AthleteProfile.user_id)
                    .where(
                        AthleteProfile.athlete_id
                        == athlete_id,
                    )
                )

            if user_id is None:
                return []

            items = session.scalars(
                select(ImportedActivity)
                .join(
                    ExternalIntegration,
                    ExternalIntegration.id
                    == ImportedActivity.integration_id,
                )
                .where(
                    ExternalIntegration.user_id
                    == user_id,
                )
                .order_by(
                    ImportedActivity.start_at.asc(),
                    ImportedActivity.id.asc(),
                )
            ).all()

            for item in items:
                session.expunge(item)

            return items

    def get_for_integration(self, activity_id, integration_id):
        session = SessionLocal()
        item = session.scalars(
            select(ImportedActivity).where(
                ImportedActivity.id == activity_id,
                ImportedActivity.integration_id == integration_id,
            )
        ).first()
        session.close()
        return item
