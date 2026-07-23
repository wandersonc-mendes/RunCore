from datetime import datetime

from sqlalchemy import select

from database.database import SessionLocal
from models.strava_connection import StravaConnection


class StravaConnectionRepository:

    def get_by_athlete_id(
        self,
        athlete_id: int,
    ) -> StravaConnection | None:

        with SessionLocal() as session:

            statement = (
                select(StravaConnection)
                .where(
                    StravaConnection.athlete_id == athlete_id,
                )
            )

            connection = session.scalar(
                statement,
            )

            if connection is not None:
                session.expunge(connection)

            return connection

    def get_by_strava_athlete_id(
        self,
        strava_athlete_id: int,
    ) -> StravaConnection | None:

        with SessionLocal() as session:

            statement = (
                select(StravaConnection)
                .where(
                    StravaConnection.strava_athlete_id
                    == strava_athlete_id,
                )
            )

            connection = session.scalar(
                statement,
            )

            if connection is not None:
                session.expunge(connection)

            return connection

    def create_or_update(
        self,
        athlete_id: int,
        strava_athlete_id: int,
        access_token: str,
        refresh_token: str,
        expires_at: int,
        scope: str = "",
        athlete_firstname: str = "",
        athlete_lastname: str = "",
        athlete_profile_url: str = "",
    ) -> StravaConnection:

        with SessionLocal() as session:

            statement = (
                select(StravaConnection)
                .where(
                    StravaConnection.athlete_id == athlete_id,
                )
            )

            connection = session.scalar(
                statement,
            )

            if connection is None:
                connection = StravaConnection(
                    athlete_id=athlete_id,
                    strava_athlete_id=strava_athlete_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    scope=scope,
                    athlete_firstname=athlete_firstname,
                    athlete_lastname=athlete_lastname,
                    athlete_profile_url=athlete_profile_url,
                )

                session.add(
                    connection,
                )

            else:
                connection.strava_athlete_id = (
                    strava_athlete_id
                )

                connection.access_token = (
                    access_token
                )

                connection.refresh_token = (
                    refresh_token
                )

                connection.expires_at = (
                    expires_at
                )

                connection.scope = (
                    scope
                )

                connection.athlete_firstname = (
                    athlete_firstname
                )

                connection.athlete_lastname = (
                    athlete_lastname
                )

                connection.athlete_profile_url = (
                    athlete_profile_url
                )

                connection.updated_at = datetime.now()

            session.commit()
            session.refresh(connection)
            session.expunge(connection)

            return connection

    def update_tokens(
        self,
        athlete_id: int,
        access_token: str,
        refresh_token: str,
        expires_at: int,
    ) -> StravaConnection | None:

        with SessionLocal() as session:

            statement = (
                select(StravaConnection)
                .where(
                    StravaConnection.athlete_id == athlete_id,
                )
            )

            connection = session.scalar(
                statement,
            )

            if connection is None:
                return None

            connection.access_token = access_token
            connection.refresh_token = refresh_token
            connection.expires_at = expires_at
            connection.updated_at = datetime.now()

            session.commit()
            session.refresh(connection)
            session.expunge(connection)

            return connection

    def mark_synced(
        self,
        athlete_id: int,
    ) -> StravaConnection | None:

        with SessionLocal() as session:

            statement = (
                select(StravaConnection)
                .where(
                    StravaConnection.athlete_id == athlete_id,
                )
            )

            connection = session.scalar(
                statement,
            )

            if connection is None:
                return None

            connection.last_sync_at = datetime.now()
            connection.updated_at = datetime.now()

            session.commit()
            session.refresh(connection)
            session.expunge(connection)

            return connection

    def delete_by_athlete_id(
        self,
        athlete_id: int,
    ) -> bool:

        with SessionLocal() as session:

            statement = (
                select(StravaConnection)
                .where(
                    StravaConnection.athlete_id == athlete_id,
                )
            )

            connection = session.scalar(
                statement,
            )

            if connection is None:
                return False

            session.delete(connection)
            session.commit()

            return True