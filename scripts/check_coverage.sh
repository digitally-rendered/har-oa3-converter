#!/bin/bash

# Run tests with coverage
echo "Running tests with coverage..."
poetry run pytest --cov=har_oa3_converter --cov-report=term --cov-report=html --cov-report=xml

# Get the coverage percentage
COVERAGE=$(poetry run coverage report | grep TOTAL | awk '{print $NF}' | sed 's/%//')
echo "Current coverage: $COVERAGE%"

# Generate coverage badge
python scripts/generate_coverage_badge.py

# Check if coverage meets the target
if (( $(echo "$COVERAGE < 100" | bc -l) )); then
  echo "⚠️  Warning: Coverage is below 100%. Current coverage: $COVERAGE%"
  echo "📊 Coverage report available in htmlcov/index.html"
  echo "🔍 Check the report to identify which parts of the code need more tests."
  exit 1
else
  echo "✅ Great! Coverage is at 100%."
  exit 0
fi
