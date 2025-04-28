# Dockerfile for ETL processes
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy only files necessary for dependency installation
COPY etl/pyproject.toml etl/poetry.lock* /app/etl/

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    cd etl && poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application code
COPY etl/src /app/etl/src

# Command to run the application (adjust as needed)
CMD ["python", "etl/src/cli.py"]
