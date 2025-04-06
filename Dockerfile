# Accept Python version as a build argument with 3.11 as default
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.6.1

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy project
COPY . /app/

# Install the package with CLI entrypoints
RUN poetry install --no-interaction --no-ansi

# Make sure the CLI commands are available in PATH
RUN pip install -e . && \
    python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir --upgrade setuptools wheel

# Verify CLI commands are available
RUN which har2oa3 && \
    which api-convert && \
    which api-server && \
    har2oa3 --help || (echo "CLI commands not properly installed" && exit 1)

# Create non-root user for security
RUN useradd -m appuser
USER appuser

# Default command when no arguments provided
CMD ["har2oa3", "--help"]

