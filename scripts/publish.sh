#!/bin/bash
# Script to build and publish the package to PyPI

# Build the package
echo "Building package..."
poetry build

# Verify the built package
echo "Verifying built package..."
ls -l dist/

# Publish to PyPI (uncomment when ready to publish)
echo "To publish to PyPI, uncomment the next line when ready"
# poetry publish

# Publish to TestPyPI for testing
echo "To publish to TestPyPI, uncomment the next line when ready"
# poetry publish -r testpypi

echo "Done!"
