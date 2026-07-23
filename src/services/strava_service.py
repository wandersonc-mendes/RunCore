from urllib.parse import urlencode

import requests

from config import STRAVA_CLIENT_ID
from config import STRAVA_CLIENT_SECRET
from config import STRAVA_REDIRECT_URI
from config import validate_strava_configuration


class StravaService:

    AUTHORIZATION_URL = (
        "https://www.strava.com/oauth/authorize"
    )

    TOKEN_URL = (
        "https://www.strava.com/oauth/token"
    )

    API_BASE_URL = (
        "https://www.strava.com/api/v3"
    )

    DEFAULT_SCOPE = (
        "read,activity:read_all"
    )


    def build_authorization_url(
        self,
        state: str,
        scope: str | None = None,
        approval_prompt: str = "auto",
    ) -> str:

        validate_strava_configuration()

        parameters = {
            "client_id": STRAVA_CLIENT_ID,
            "redirect_uri": STRAVA_REDIRECT_URI,
            "response_type": "code",
            "approval_prompt": approval_prompt,
            "scope": scope or self.DEFAULT_SCOPE,
            "state": state,
        }

        return (
            f"{self.AUTHORIZATION_URL}"
            f"?{urlencode(parameters)}"
        )


    def exchange_code_for_tokens(
        self,
        code: str,
    ) -> dict:

        validate_strava_configuration()

        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
            timeout=20,
        )

        self._raise_for_error(
            response,
            operation=(
                "trocar o código de autorização "
                "pelos tokens"
            ),
        )

        return response.json()


    def refresh_tokens(
        self,
        refresh_token: str,
    ) -> dict:

        validate_strava_configuration()

        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=20,
        )

        self._raise_for_error(
            response,
            operation="renovar o acesso ao Strava",
        )

        return response.json()


    def get_logged_in_athlete(
        self,
        access_token: str,
    ) -> dict:

        response = requests.get(
            f"{self.API_BASE_URL}/athlete",
            headers={
                "Authorization": (
                    f"Bearer {access_token}"
                ),
            },
            timeout=20,
        )

        self._raise_for_error(
            response,
            operation=(
                "consultar o perfil do atleta "
                "no Strava"
            ),
        )

        return response.json()


    @staticmethod
    def _raise_for_error(
        response: requests.Response,
        operation: str,
    ) -> None:

        if response.ok:
            return

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        message = (
            payload.get("message")
            or payload.get("error")
            or response.text
            or "Resposta inválida do Strava"
        )

        raise RuntimeError(
            f"Não foi possível {operation}: "
            f"{message} "
            f"(HTTP {response.status_code})"
        )