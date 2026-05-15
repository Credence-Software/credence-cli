"""Stdout JSON output for CLI commands."""

from __future__ import annotations

import json
import sys
from typing import Any


def write_json(value: Any) -> None:
    """Write a command result to stdout as formatted JSON."""
    json.dump(value, sys.stdout, indent=2)
    sys.stdout.write("\n")
