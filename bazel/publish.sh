#!/bin/bash
set -e

# Publish Poetry package to PyPI using Bazel
echo "Publishing Poetry package to PyPI..."
cd "$(git rev-parse --show-toplevel)"

# Build the package first
./bazel/build.sh

# Check if PyPI token is available
if [ -z "$POETRY_PYPI_TOKEN_PYPI" ]; then
    echo "Error: POETRY_PYPI_TOKEN_PYPI environment variable not set."
    echo "Please set your PyPI token with: export POETRY_PYPI_TOKEN_PYPI='your-token'"
    exit 1
fi

# Publish to PyPI
echo "Publishing package to PyPI..."
poetry publish

echo "Package published successfully to PyPI."
