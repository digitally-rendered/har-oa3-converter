#!/bin/bash

set -e

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

# Check if Docker is available
if ! docker info >/dev/null 2>&1; then
    echo "\033[1;31m⚠️  ALERT: Docker is not running or not available\033[0m"
    echo "\033[1;34mℹ️  This script requires Docker to run the tests\033[0m"
    echo "\033[1;34mℹ️  Please start Docker daemon and try again\033[0m"
    echo "\033[1;34mℹ️  Falling back to local testing mode without Docker\033[0m"
    echo "\033[1;34mℹ️  Running: pytest tests/ --cov=har_oa3_converter -xvs -n auto\033[0m"
    poetry run pytest tests/ --cov=har_oa3_converter --cov-report=term-missing --cov-report=html:./reports/coverage --cov-report=xml:./reports/coverage.xml --html=./reports/html/report.html --json-report --json-report-file=./reports/json/report.json --cov-fail-under=100 -xvs -n auto
    exit $?
fi

# Build the Docker image if it doesn't exist
if ! docker image inspect har-oa3-converter:latest >/dev/null 2>&1; then
    echo "Building Docker image..."
    docker build -t har-oa3-converter:latest .
fi

# Create reports directories locally first
echo "Creating report directories..."
mkdir -p ./docker-reports/html ./docker-reports/coverage ./docker-reports/json

# Create test container with development dependencies and mount volumes
echo "Creating test container..."
docker run --name har-oa3-test -d \
  -v "$(pwd):/app:delegated" \
  -v "$(pwd)/docker-reports:/app/reports:delegated" \
  har-oa3-converter:latest tail -f /dev/null

# Set proper permissions inside the container
echo "Setting up permissions..."
docker exec -u appuser har-oa3-test bash -c "chown -R appuser:appuser /app/reports 2>/dev/null || true"

# Run code quality checks first - skip the fix_pylint_issues.py file
echo "Running black code formatting check..."
docker exec -u appuser har-oa3-test bash -c "cd /app && \
    poetry config virtualenvs.create false && \
    poetry install && \
    black --check . --exclude '/app/scripts/fix_pylint_issues.py|/app/.tox/|/app/.git/'"

echo "Running pylint code quality check (optional)..."
docker exec -u appuser har-oa3-test bash -c "cd /app && \
    pylint har_oa3_converter/ tests/ --fail-under=9.0 --ignore=scripts/fix_pylint_issues.py || echo \"⚠️  Pylint check failed but continuing with tests\"
"

# Run tests inside container with coverage and reports
echo "Running tests with coverage..."
docker exec -u appuser har-oa3-test bash -c "cd /app && \
    poetry config virtualenvs.create false && \
    poetry install && \
    COVERAGE_FILE=/app/reports/.coverage python -m pytest \
    --cov=har_oa3_converter \
    --cov-report=term-missing \
    --cov-report=html:/app/reports/coverage \
    --cov-report=xml:/app/reports/coverage.xml \
    --html=/app/reports/html/report.html \
    --json-report \
    --json-report-file=/app/reports/json/report.json \
    --cov-fail-under=100 \
    -xvs \
    -n auto \
    tests/"

# Copy report files back
echo "Copying test reports from container..."
docker cp har-oa3-test:/app/reports ./docker-reports

# Clean up
echo "Cleaning up container..."
docker stop har-oa3-test
docker rm har-oa3-test

echo -e "\nDocker test run complete!"
echo -e "Test reports are available in the docker-reports directory\n"
