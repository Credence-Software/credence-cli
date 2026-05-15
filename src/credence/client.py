"""HTTP client for the Credence platform API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from credence import endpoints
from credence.errors import CredenceCliError

CREDENCE_TOKEN_ENV_VAR = "CREDENCE_TOKEN"
CREDENCE_API_URL_ENV_VAR = "CREDENCE_API_URL"
DEFAULT_API_URL = "http://localhost:8000"


@dataclass(frozen=True)
class CliSession:
    """Authenticated CLI session metadata."""

    token: str
    user_email: str | None = None


def _extract_error_detail(response: httpx.Response) -> str | None:
    """Extract a readable error detail from an API response."""
    try:
        payload = response.json()
    except ValueError:
        return None

    detail = payload.get("detail")
    return detail if isinstance(detail, str) and detail else None


def _parse_json_response(response: httpx.Response, *, invalid_response_message: str) -> Any:
    """Parse a JSON response and raise a readable error when invalid."""
    try:
        return response.json()
    except ValueError as exc:
        raise CredenceCliError(invalid_response_message) from exc


class CredenceClient:
    """Call Credence HTTP API endpoints with token authentication."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = (base_url or os.getenv(CREDENCE_API_URL_ENV_VAR) or DEFAULT_API_URL).rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(transport=transport, timeout=timeout)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> CredenceClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def authenticate(self, *, email: str, password: str) -> CliSession:
        """Obtain an API token using email and password."""
        url = f"{self._base_url}{endpoints.AUTHENTICATE}"
        try:
            response = self._client.post(url, json={"email": email, "password": password})
        except httpx.RequestError as exc:
            msg = f"Unable to reach Credence API at '{self._base_url}'."
            raise CredenceCliError(msg) from exc

        if response.status_code == 404:
            raise CredenceCliError("Invalid email or password.")

        if not response.is_success:
            detail = _extract_error_detail(response)
            msg = detail or f"Credence API authentication failed with status {response.status_code}."
            raise CredenceCliError(msg)

        payload = _parse_json_response(
            response,
            invalid_response_message="Credence API returned an invalid authentication response.",
        )

        token = payload.get("token")
        if not isinstance(token, str) or not token.strip():
            raise CredenceCliError("Credence API returned an invalid authentication response.")

        user_email = payload.get("user")
        return CliSession(
            token=token,
            user_email=user_email if isinstance(user_email, str) else None,
        )

    def get_json(self, *, path: str, token: str | None = None, params: dict[str, Any] | None = None) -> Any:
        """GET a JSON response from an authenticated endpoint."""
        normalized_path = f"/{path.lstrip('/')}"
        url = f"{self._base_url}{normalized_path}"
        cli_token = (token or os.getenv(CREDENCE_TOKEN_ENV_VAR, "")).strip()

        if not cli_token:
            msg = f"CLI token is required. Set {CREDENCE_TOKEN_ENV_VAR} or pass --token."
            raise CredenceCliError(msg)

        try:
            response = self._client.get(
                url,
                headers={"Authorization": f"Token {cli_token}"},
                params=params,
            )
        except httpx.RequestError as exc:
            msg = f"Unable to reach Credence API at '{self._base_url}'."
            raise CredenceCliError(msg) from exc

        if not response.is_success:
            detail = _extract_error_detail(response)
            msg = detail or f"Credence API request to '{normalized_path}' failed with status {response.status_code}."
            raise CredenceCliError(msg)

        return _parse_json_response(response, invalid_response_message="Credence API returned an invalid response.")
