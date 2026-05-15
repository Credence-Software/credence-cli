# Installation

## Stable release

To install Credence CLI, run this command in your terminal:

```sh
uv add credence
```

Or if you prefer to use `pip`:

```sh
pip install credence
```

## From source

The source files for Credence CLI can be downloaded from the [GitHub repository](https://github.com/Credence-Software/credence-cli).

You can either clone the public repository:

```sh
git clone https://github.com/Credence-Software/credence-cli.git
```

Or download the [tarball](https://github.com/Credence-Software/credence-cli/tarball/main):

```sh
curl -OJL https://github.com/Credence-Software/credence-cli/tarball/main
```

Once you have a copy of the source, you can install it with:

```sh
cd credence-cli
uv sync
```

To install the CLI into your environment:

```sh
uv tool install --editable .
```
