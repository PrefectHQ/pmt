# pmt

`pmt` is a command line tool designed to aid in the migration between different versions of the Prefect Python API.

## Installation

`pmt` can be installed via pip:

```bash
pip install git+https://github.com/PrefectHQ/pmt.git
```

## Usage

Generate new code for a `Deployment.build_from_flow`` call:

```bash
pmt migrate build-from-flow path/to/script.py
```

## Development

- Install [poetry](https://python-poetry.org/docs/#installation)
- Clone this repo
- Run `poetry install` to create a virtual environment, install dependencies, and install `pmt` in editable mode
