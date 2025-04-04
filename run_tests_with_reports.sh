#!/bin/bash

# Create reports directory if it doesn't exist
mkdir -p reports/html reports/json

# Run tests with all report formats and parallel execution using pytest-xdist
poetry run pytest \
  --junitxml=reports/junit.xml \
  --html=reports/html/report.html \
  --json-report \
  --json-report-file=reports/json/report.json \
  --cov=har_oa3_converter \
  --cov-report=term-missing \
  --cov-report=html:reports/coverage \
  --cov-report=xml:reports/coverage.xml \
  --cov-fail-under=100 \
  -xvs \
  -n auto \
  "$@"

# Print report locations
echo "\nTest Reports Generated:\n"
echo "JUnit XML Report: reports/junit.xml"
echo "HTML Report: reports/html/report.html"
echo "JSON Report: reports/json/report.json"
echo "Coverage HTML Report: reports/coverage/index.html"
echo "Coverage XML Report: reports/coverage.xml"

# Print coverage status
if [ $? -eq 0 ]; then
  echo "\n✅ All tests passed with 100% coverage!"
else
  echo "\n❌ Tests completed but coverage is below 100% - see report for details"
fi
