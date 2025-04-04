#!/bin/bash
set -e

# Build the Poetry package using Bazel
echo "Building Poetry package..."
cd "$(git rev-parse --show-toplevel)"

# First ensure all dependencies are updated
poetry lock --no-update

# Clean any previous build artifacts
rm -rf dist/

# Build the package using Poetry
poetry build

echo "Package built successfully. Artifacts in ./dist/"
ls -la dist/
