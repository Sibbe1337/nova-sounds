# Nova Insights Platform (NIP) - Monorepo

This repository contains the code for the Nova Insights Platform, structured as a monorepo during the initial development phase.

## Structure

- `/etl`: Data ingestion pipelines (Meltano, planned custom `tap-chartmetric`, Cloud Run jobs), Dockerfiles, Python source (`etl/src`), and tests (`etl/tests`).
- `/analytics`: dbt project for data warehousing and modeling (`analytics/dbt`).
- `/infra`: Terraform configurations for infrastructure provisioning.
- `/services`: Cloud Functions, APIs, and related Python source (`services/src`).

## Tooling

- **Dependency Management:** Poetry (see `pyproject.toml` at root, `/etl`, and `/services`).
- **Linting/Formatting:** pre-commit with Black, isort, ruff (Python) and SQLFluff (SQL).
- **Containerization:** Docker (see `etl/Dockerfile`).

## Development

Use the included Dev Container (`.devcontainer/devcontainer.json`) for a consistent environment.

Run `pre-commit install` once to set up the git hooks.
Run `poetry install` in the root, `etl`, and `services` directories to install dependencies.
