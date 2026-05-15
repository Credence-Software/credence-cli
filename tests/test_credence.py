"""Tests for Credence CLI and HTTP client."""

from __future__ import annotations

import io
import json
import sys
from typing import Any

import httpx
import pytest
import typer
from typer.testing import CliRunner

from credence import cli
from credence.client import CredenceClient
from credence.errors import CredenceCliError
from credence.filters import parse_public_ids


def _json_response(data: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=data)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_parse_public_ids_none() -> None:
    assert parse_public_ids(None) is None
    assert parse_public_ids([]) is None


def test_parse_public_ids_comma_and_repeat() -> None:
    assert parse_public_ids(["a,b", "c"]) == ["a", "b", "c"]


def test_parse_public_ids_empty_raises() -> None:
    with pytest.raises(CredenceCliError, match="non-empty"):
        parse_public_ids([""])


def test_client_authenticate_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/authenticate/"
        body = json.loads(request.content.decode())
        assert body["email"] == "u@example.com"
        assert body["password"] == "secret"
        return _json_response({"token": "tok", "user": "u@example.com"})

    client = CredenceClient(base_url="http://api.test", transport=httpx.MockTransport(handler))
    session = client.authenticate(email="u@example.com", password="secret")
    assert session.token == "tok"
    assert session.user_email == "u@example.com"


def test_client_authenticate_invalid_password() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = CredenceClient(base_url="http://api.test", transport=httpx.MockTransport(handler))
    with pytest.raises(CredenceCliError, match="Invalid email or password"):
        client.authenticate(email="u@example.com", password="wrong")


def test_client_get_json_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CREDENCE_TOKEN", raising=False)
    client = CredenceClient(base_url="http://api.test", transport=httpx.MockTransport(lambda r: _json_response({})))
    with pytest.raises(CredenceCliError, match="CLI token is required"):
        client.get_json(path="/api/x/", token=None)


def test_client_get_json_with_token_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Token mytoken"
        assert request.url.path == "/api/portfolio/portfolios/"
        return _json_response([{"id": 1}])

    client = CredenceClient(base_url="http://api.test", transport=httpx.MockTransport(handler))
    data = client.get_json(path="/api/portfolio/portfolios/", token="mytoken")
    assert data == [{"id": 1}]


def test_get_all_properties_paginates() -> None:
    calls: list[tuple[int, int]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        offset = int(params.get("offset", "0"))
        limit = int(params.get("limit", "0"))
        calls.append((offset, limit))
        if offset == 0:
            return _json_response({"results": [{"n": 1}], "count": 2})
        return _json_response({"results": [{"n": 2}], "count": 2})

    client = CredenceClient(base_url="http://api.test", transport=httpx.MockTransport(handler))
    out = cli._get_all_properties(client=client, token="t", params=None)
    assert out == [{"n": 1}, {"n": 2}]
    assert calls == [(0, 100), (1, 100)]


def test_login_cli_success(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"token": "abc", "user": "u@example.com"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        cli,
        "_make_client",
        lambda api_url=None: CredenceClient(base_url="http://api.test", transport=transport),
    )

    result = runner.invoke(
        cli.app,
        ["--api-url", "http://api.test", "login", "--email", "u@example.com", "--password-stdin"],
        input="secret\n",
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"token": "abc", "user": "u@example.com"}


def test_login_cli_password_stdin(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert body["password"] == "from-stdin"
        return _json_response({"token": "x"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        cli,
        "_make_client",
        lambda api_url=None: CredenceClient(base_url="http://api.test", transport=transport),
    )

    result = runner.invoke(
        cli.app,
        ["login", "--email", "u@example.com", "--password-stdin"],
        input="from-stdin\n",
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["token"] == "x"


def test_login_cli_api_error_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda r: httpx.Response(500, json={"detail": "server boom"}))
    monkeypatch.setattr(
        cli,
        "_make_client",
        lambda api_url=None: CredenceClient(base_url="http://api.test", transport=transport),
    )
    monkeypatch.setattr(sys, "argv", ["credence", "login", "--email", "u@example.com", "--password-stdin"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("pw\n"))

    with pytest.raises(typer.Exit) as exc_info:
        cli.main()
    assert exc_info.value.exit_code == 2


def test_portfolios_cli(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "public_id" in str(request.url) or request.url.params.get_list("public_id")
        return _json_response([{"name": "P1"}])

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        cli,
        "_make_client",
        lambda api_url=None: CredenceClient(base_url="http://api.test", transport=transport),
    )

    result = runner.invoke(
        cli.app,
        ["portfolios", "--token", "t", "--public-id", "a,b"],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout) == [{"name": "P1"}]
