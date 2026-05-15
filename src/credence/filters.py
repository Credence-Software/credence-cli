"""Filter parsing helpers for the Credence CLI."""

from __future__ import annotations

from credence.errors import CredenceCliError


def parse_public_ids(raw_values: list[str] | None, *, option_name: str = "--public-id") -> list[str] | None:
    """Parse repeated and comma-separated public ID filters."""
    if not raw_values:
        return None

    public_ids = [item.strip() for value in raw_values for item in value.split(",")]
    public_ids = [public_id for public_id in public_ids if public_id]

    if not public_ids:
        msg = f"At least one non-empty public ID is required when using {option_name}."
        raise CredenceCliError(msg)

    return public_ids
