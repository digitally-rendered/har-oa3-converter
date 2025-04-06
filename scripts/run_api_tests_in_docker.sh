#!/bin/bash

set -e

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

# Build the Docker image if it doesn't exist
if ! docker image inspect har-oa3-converter:latest >/dev/null 2>&1; then
    echo "Building Docker image..."
    docker build -t har-oa3-converter:latest .
fi

# Check if Docker is available
if ! docker info >/dev/null 2>&1; then
    echo "\033[1;31m⚠️  ALERT: Docker is not running or not available\033[0m"
    echo "\033[1;34mℹ️  This script requires Docker to run the API tests\033[0m"
    echo "\033[1;34mℹ️  Please start Docker daemon and try again\033[0m"
    echo "\033[1;34mℹ️  Falling back to local API testing mode without Docker\033[0m"
    echo "\033[1;34mℹ️  Running: pytest tests/docker/test_docker_api.py tests/docker/test_docker_schema_validation.py -xvs -n auto\033[0m"
    poetry run pytest tests/docker/test_docker_api.py tests/docker/test_docker_schema_validation.py -xvs --cov=har_oa3_converter --cov-report=term-missing --cov-report=html:./reports/api-tests/coverage --cov-report=xml:./reports/api-tests/coverage.xml --html=./reports/api-tests/html/report.html --json-report --json-report-file=./reports/api-tests/json/report.json --cov-fail-under=100
    exit $?
fi

# Clean up any existing containers
echo "Cleaning up any existing containers..."
docker rm -f har-oa3-api-test 2>/dev/null || true

# Create report directories
mkdir -p ./docker-reports/api-tests/coverage \
        ./docker-reports/api-tests/html \
        ./docker-reports/api-tests/json

# Run code quality checks first
echo "Running black code formatting check..."
poetry run black --check .

echo "Running pylint code quality check..."
poetry run pylint har_oa3_converter/ tests/ --fail-under=9.0

# Run the API tests
echo "Running API tests against Docker container..."
poetry run pytest \
    tests/docker/test_docker_api.py \
    -xvs \
    -n auto \
    --cov=har_oa3_converter \
    --cov-report=term-missing \
    --cov-report=html:./docker-reports/api-tests/coverage \
    --cov-report=xml:./docker-reports/api-tests/coverage.xml \
    --html=./docker-reports/api-tests/html/report.html \
    --json-report \
    --json-report-file=./docker-reports/api-tests/json/report.json \
    --cov-fail-under=100

echo -e "\nAPI Docker test run complete!"
echo -e "API Test reports are available in the docker-reports/api-tests directory\n"
echo -e "HTML Coverage Report: docker-reports/api-tests/coverage/index.html"
echo -e "HTML Test Report: docker-reports/api-tests/html/report.html"
echo -e "JSON Test Report: docker-reports/api-tests/json/report.json\n"
