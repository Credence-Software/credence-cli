# Usage

The `credence` command provides subcommands for authenticating and reading data from the Credence HTTP API.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `CREDENCE_API_URL` | Base URL of the API (default: `http://localhost:8000`). |
| `CREDENCE_TOKEN` | API token used by list commands when `--token` is omitted. |

You can override the API base URL per invocation with the global option `--api-url`.

## Commands

### `login`

Authenticate with email and password and print a JSON object containing `token` (and `user` when returned by the API).

```bash
credence login --email you@example.com
```

Non-interactive environments must read the password from stdin:

```bash
printf '%s' "$CREDENCE_PASSWORD" | credence login --email you@example.com --password-stdin
```

### `portfolios`

List portfolios for the authenticated user (JSON array on stdout).

```bash
credence portfolios --token "$CREDENCE_TOKEN"
```

Optional filters (repeat flags or use comma-separated values):

```bash
credence portfolios --token "$CREDENCE_TOKEN" --public-id abc --public-id def
credence portfolios --token "$CREDENCE_TOKEN" --public-id abc,def
```

### `properties`

List properties, following paginated API responses until all pages are merged (JSON array on stdout).

```bash
credence properties --token "$CREDENCE_TOKEN"
credence properties --token "$CREDENCE_TOKEN" --portfolio PORT_PUBLIC_ID --property PROP_PUBLIC_ID
```

### `rent-roll`

List rent-roll rows the user can access.

```bash
credence rent-roll --token "$CREDENCE_TOKEN"
credence rent-roll --token "$CREDENCE_TOKEN" --tenant-name "Acme"
credence rent-roll --token "$CREDENCE_TOKEN" --portfolio-public-id PID --lease-public-id LID
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Expected error (e.g. invalid credentials, missing token, API error with a readable message) |

## Python import

This package is primarily a CLI. You may import it to reuse the HTTP client:

```python
from credence.client import CredenceClient

with CredenceClient(base_url="https://example.com") as client:
    session = client.authenticate(email="...", password="...")
```
