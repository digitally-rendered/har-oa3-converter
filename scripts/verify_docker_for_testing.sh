#!/bin/bash

set -e

echo "=== Verifying Docker for har-oa3-converter Testing ==="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "\u274c Docker command not found. Please run ./scripts/setup_rancher_desktop.sh first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &>/dev/null; then
    echo "\u274c Docker daemon is not running. Please start Rancher Desktop."
    exit 1
fi

echo "\u2705 Docker daemon is running."

# Create a temporary Dockerfile for testing
TEMP_DIR=$(mktemp -d)
TEST_DOCKERFILE="${TEMP_DIR}/Dockerfile.test"

cat > "${TEST_DOCKERFILE}" << 'EOF'
FROM python:3.11-slim

RUN pip install pytest pytest-cov pytest-html pytest-json-report pytest-xdist black pylint

WORKDIR /app
COPY . .

CMD ["echo", "Docker test environment ready!"]
EOF

# Build a test image
echo "Building a test Docker image to verify Python testing environment..."
docker build -t har-oa3-test-verify -f "${TEST_DOCKERFILE}" .

# Run container to verify pytest and testing tools
echo "Verifying pytest and testing tools in container..."
docker run --rm har-oa3-test-verify bash -c "\
    python -m pytest --version && \
    python -m pytest --cov --version && \
    python -m pytest --html --version && \
    python -m pytest --json-report --version && \
    python -m pytest --xdist --version && \
    black --version && \
    pylint --version"

# Clean up
rm -rf "${TEMP_DIR}"
docker rmi har-oa3-test-verify

echo "\n\u2705 Docker environment is properly configured for har-oa3-converter testing!"
echo "\nYou can now run:\n"
echo "  ./scripts/run_tests_in_docker.sh     # Run all tests with 100% coverage target"
echo "  pytest tests/docker/ -v              # Run Docker-specific tests"

echo "\nTest reports will be generated in the docker-reports directory with:\n"
echo "  - HTML coverage reports (reports/coverage/index.html)"
echo "  - XML coverage reports (reports/coverage.xml)"
echo "  - HTML test reports (reports/html/report.html)"
echo "  - JSON test reports (reports/json/report.json)"
