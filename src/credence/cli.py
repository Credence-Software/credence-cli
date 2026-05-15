"""Typer CLI for the Credence platform."""

from __future__ import annotations

import getpass
import sys
from dataclasses import dataclass
from typing import Annotated, Any

import typer

from credence import endpoints
from credence.client import CredenceClient
from credence.errors import CredenceCliError
from credence.filters import parse_public_ids
from credence.output import write_json

CREDENCE_WEB = "https://credence-software.com"

app = typer.Typer(
    no_args_is_help=True,
    epilog=f"Learn more about Credence at {CREDENCE_WEB}",
)


@dataclass
class CLIState:
    """Per-invocation CLI context."""

    client: CredenceClient


def _make_client(api_url: str | None) -> CredenceClient:
    """Construct the HTTP client (patch in tests)."""
    return CredenceClient(base_url=api_url)


@app.callback()
def main_callback(
    ctx: typer.Context,
    api_url: Annotated[
        str | None,
        typer.Option(
            "--api-url",
            envvar="CREDENCE_API_URL",
            help="Credence API base URL (overrides CREDENCE_API_URL).",
        ),
    ] = None,
) -> None:
    """Credence command-line tools."""
    ctx.obj = CLIState(client=_make_client(api_url))


def _get_all_properties(*, client: CredenceClient, token: str | None, params: dict[str, object] | None) -> list[Any]:
    """Read all pages from the property list endpoint."""
    base_params = dict(params or {})
    offset = 0
    properties: list[Any] = []

    while True:
        response = client.get_json(
            path=endpoints.LIST_PROPERTIES,
            token=token,
            params={
                **base_params,
                "limit": 100,
                "offset": offset,
            },
        )

        if isinstance(response, list):
            return response

        if not isinstance(response, dict):
            raise CredenceCliError("Credence API returned an invalid property list response.")

        page_results = response.get("results")
        count = response.get("count")
        if not isinstance(page_results, list) or not isinstance(count, int):
            raise CredenceCliError("Credence API returned an invalid property list response.")

        properties.extend(page_results)
        offset += len(page_results)
        if offset >= count or not page_results:
            return properties


@app.command()
def login(
    ctx: typer.Context,
    email: Annotated[str, typer.Option("--email", help="Credence user email.")],
    password_stdin: Annotated[
        bool,
        typer.Option("--password-stdin", help="Read the password from stdin instead of prompting."),
    ] = False,
) -> None:
    """Authenticate and print an API token as JSON."""
    password = _read_password(password_stdin=password_stdin)
    state: CLIState = ctx.obj
    session = state.client.authenticate(email=email, password=password)

    payload: dict[str, str] = {"token": session.token}
    if session.user_email is not None:
        payload["user"] = session.user_email

    write_json(payload)


def _read_password(*, password_stdin: bool) -> str:
    """Read the user's password from stdin or an interactive prompt."""
    if password_stdin:
        password = sys.stdin.read().rstrip("\r\n")
    else:
        if not sys.stdin.isatty():
            raise CredenceCliError("Use --password-stdin when running non-interactively.")
        password = getpass.getpass("Credence password: ")

    if not password:
        raise CredenceCliError("Password is required.")
    return password


@app.command()
def portfolios(
    ctx: typer.Context,
    token: Annotated[
        str | None,
        typer.Option("--token", envvar="CREDENCE_TOKEN", help="API auth token (defaults to CREDENCE_TOKEN)."),
    ] = None,
    public_id: Annotated[
        list[str],
        typer.Option("--public-id", help="Filter by portfolio public ID (repeat or comma-separated)."),
    ] = [],
) -> None:
    """List portfolios accessible to the authenticated user."""
    state: CLIState = ctx.obj
    public_ids = parse_public_ids(public_id)
    params: dict[str, Any] | None = {"public_id": public_ids} if public_ids else None
    portfolios = state.client.get_json(path=endpoints.LIST_PORTFOLIOS, token=token, params=params)

    if not isinstance(portfolios, list):
        raise CredenceCliError("Credence API returned an invalid portfolio list response.")

    write_json(portfolios)


@app.command()
def properties(
    ctx: typer.Context,
    token: Annotated[
        str | None,
        typer.Option("--token", envvar="CREDENCE_TOKEN", help="API auth token (defaults to CREDENCE_TOKEN)."),
    ] = None,
    portfolio: Annotated[
        list[str],
        typer.Option("--portfolio", help="Filter by portfolio public ID (repeat or comma-separated)."),
    ] = [],
    property_id: Annotated[
        list[str],
        typer.Option("--property", help="Filter by property public ID (repeat or comma-separated)."),
    ] = [],
) -> None:
    """List properties accessible to the authenticated user."""
    state: CLIState = ctx.obj
    portfolio_public_ids = parse_public_ids(portfolio, option_name="--portfolio")
    property_public_ids = parse_public_ids(property_id, option_name="--property")
    params: dict[str, object] = {}
    if portfolio_public_ids:
        params["portfolio"] = portfolio_public_ids
    if property_public_ids:
        params["public_id"] = property_public_ids

    result = _get_all_properties(
        client=state.client,
        token=token,
        params=params or None,
    )

    write_json(result)


@app.command("rent-roll")
def rent_roll(
    ctx: typer.Context,
    token: Annotated[
        str | None,
        typer.Option("--token", envvar="CREDENCE_TOKEN", help="API auth token (defaults to CREDENCE_TOKEN)."),
    ] = None,
    portfolio_public_id: Annotated[
        list[str],
        typer.Option("--portfolio-public-id", help="Filter by portfolio public ID (repeat or comma-separated)."),
    ] = [],
    property_public_id: Annotated[
        list[str],
        typer.Option("--property-public-id", help="Filter by property public ID (repeat or comma-separated)."),
    ] = [],
    lease_public_id: Annotated[
        list[str],
        typer.Option("--lease-public-id", help="Filter by lease public ID (repeat or comma-separated)."),
    ] = [],
    tenant_name: Annotated[str | None, typer.Option("--tenant-name", help="Case-insensitive contains match.")] = None,
) -> None:
    """List rent-roll rows accessible to the authenticated user."""
    state: CLIState = ctx.obj
    portfolio_ids = parse_public_ids(portfolio_public_id, option_name="--portfolio-public-id")
    property_ids = parse_public_ids(property_public_id, option_name="--property-public-id")
    lease_ids = parse_public_ids(lease_public_id, option_name="--lease-public-id")

    params: dict[str, Any] = {}
    if portfolio_ids:
        params["portfolio_public_id"] = portfolio_ids
    if property_ids:
        params["property_public_id"] = property_ids
    if lease_ids:
        params["lease_public_id"] = lease_ids
    if tenant_name:
        params["tenant_name"] = tenant_name

    rent_roll_rows = state.client.get_json(
        path=endpoints.LIST_RENT_ROLL,
        token=token,
        params=params or None,
    )

    if not isinstance(rent_roll_rows, list):
        raise CredenceCliError("Credence API returned an invalid rent roll response.")

    write_json(rent_roll_rows)


def main() -> None:
    """Console entrypoint with stable exit codes."""
    try:
        app()
    except CredenceCliError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(2) from exc
    except BrokenPipeError:
        # e.g. piping to `head`
        raise typer.Exit(0) from None
