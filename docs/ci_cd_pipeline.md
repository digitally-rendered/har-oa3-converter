# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Delivery (CI/CD) pipeline for the HAR to OpenAPI Converter project.

## Overview

The project uses GitHub Actions to automate testing, linting, and publishing to PyPI. The workflow is defined in the `.github/workflows/python-package.yml` file.

## Workflow Stages

The CI/CD pipeline consists of two main jobs:

### 1. Test Job

This job runs on every push to the main branch and on every pull request:

- **Runs on multiple Python versions**: 3.8, 3.9, 3.10, 3.11
- **Steps**:
  - Checkout code
  - Set up Python environment
  - Install Poetry
  - Install project dependencies
  - Run linting with Black and isort
  - Run type checking with mypy
  - Run tests with pytest and collect coverage
  - Upload coverage report to Codecov

### 2. Publish Job

This job runs only when a version tag (e.g., `v0.1.0`) is pushed:

- **Runs only after tests pass**: Depends on the test job
- **Steps**:
  - Checkout code
  - Set up Python environment
  - Install Poetry
  - Install project dependencies
  - Build package with Poetry
  - Publish to TestPyPI (for validation)
  - Publish to PyPI

## Workflow Triggers

The pipeline is triggered by:

- **Push to main/master branches**: Runs tests only
- **Pull requests to main/master**: Runs tests only
- **Tags starting with 'v'**: Runs tests and, if successful, publishes to PyPI

## Required Secrets

For the publishing job to work, the following GitHub repository secrets must be set:

- `TEST_PYPI_API_TOKEN`: API token for TestPyPI
- `PYPI_API_TOKEN`: API token for PyPI

## Setting Up Secrets

1. Generate API tokens:
   - For PyPI: Go to https://pypi.org/manage/account/token/
   - For TestPyPI: Go to https://test.pypi.org/manage/account/token/

2. Add secrets to your GitHub repository:
   - Go to your repository on GitHub
   - Click on "Settings" > "Secrets and variables" > "Actions"
   - Click "New repository secret" and add:
     - Name: `PYPI_API_TOKEN`, Value: (your PyPI token)
     - Name: `TEST_PYPI_API_TOKEN`, Value: (your TestPyPI token)

## Release Process

To release a new version:

1. Update version in `pyproject.toml`
2. Commit changes:
   ```bash
   git add pyproject.toml
   git commit -m "bump: version to x.y.z"
   ```
3. Create a tag:
   ```bash
   git tag vx.y.z
   ```
4. Push changes and tag:
   ```bash
   git push origin main
   git push origin vx.y.z
   ```
5. Monitor the GitHub Actions workflow:
   - Go to your repository's "Actions" tab
   - Check progress of the workflow triggered by the tag

## Troubleshooting

Common issues and how to resolve them:

### Tests Failing

1. Check the specific test failures in the GitHub Actions logs
2. Run tests locally to reproduce the issue:
   ```bash
   poetry run pytest
   ```
3. Fix the issues and push changes

### Publishing Failing

1. Verify that your secrets are correctly set in GitHub
2. Ensure your version in `pyproject.toml` is not already published
3. Check that your package name is available on PyPI
4. Verify that your tag follows the format `vx.y.z`

## CI/CD Pipeline Diagram

```
┌─────────────────┐
│   Git Push      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No     ┌─────────────────┐
│  Is it a tag?   ├────────────►    Test Job     │
└────────┬────────┘            └─────────────────┘
         │ Yes
         ▼
┌─────────────────┐
│    Test Job     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No     ┌─────────────────┐
│  Tests passed?  ├────────────►   Job fails     │
└────────┬────────┘            └─────────────────┘
         │ Yes
         ▼
┌─────────────────┐
│   Publish Job   │
└─────────────────┘
```
