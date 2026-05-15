# Credence CLI

![PyPI version](https://img.shields.io/pypi/v/credence.svg)

A lightweight CLI for interacting with the Credence platform over its public HTTP API.

* GitHub: https://github.com/Credence-Software/credence-cli
* PyPI package: https://pypi.org/project/credence/
* **[Credence Software](https://credence-software.com)** — [Organization on GitHub](https://github.com/Credence-Software)
* Free software: MIT License

## Features

* `login` — obtain an API token from email and password
* `portfolios` — list portfolios (optional `public_id` filters)
* `properties` — list properties with automatic pagination (optional portfolio / property filters)
* `rent-roll` — list accessible rent-roll rows (optional portfolio, property, lease, tenant name filters)
* Global `--api-url` (or `CREDENCE_API_URL`) and `CREDENCE_TOKEN` for non-interactive use
* JSON output on stdout; stable exit codes (`2` for expected errors)

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://credence-software.github.io/credence-cli/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Development

To set up for local development:

```bash
git clone git@github.com:Credence-Software/credence-cli.git
cd credence-cli

# Install in editable mode with live updates
uv tool install --editable .
```

This installs the CLI globally but with live updates — any changes you make to the source code are immediately available when you run `credence`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

Credence CLI was created in 2026 by Credence Software.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
