# Contributing to HAR to OpenAPI Converter

Thank you for considering contributing to the HAR to OpenAPI Converter project! This document provides guidelines and instructions for development and contribution.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/har-oa3-converter.git
   cd har-oa3-converter
   ```

2. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Run the tests:
   ```bash
   poetry run pytest
   ```

## Code Style

This project uses:
- [Black](https://black.readthedocs.io/en/stable/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [mypy](https://mypy.readthedocs.io/en/stable/) for type checking

You can run these tools with:
```bash
poetry run black har_oa3_converter tests
poetry run isort har_oa3_converter tests
poetry run mypy har_oa3_converter
```

## Testing

Run the test suite with pytest:
```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=har_oa3_converter
```

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Make your changes.
3. Ensure tests pass and code style checks pass.
4. Update documentation if needed.
5. Submit a pull request.

## Continuous Integration

This project uses GitHub Actions for continuous integration and deployment:

- **Testing**: Runs on every push and pull request to the main branch.
- **Publishing**: Triggered when a new version tag (e.g., `v0.1.1`) is pushed.

### GitHub Actions Workflow

The `.github/workflows/python-package.yml` file contains two main jobs:

1. **Test**: Runs tests on multiple Python versions (3.8, 3.9, 3.10, 3.11)
   - Runs linting with black and isort
   - Checks types with mypy
   - Runs tests with pytest and collects coverage
   - Uploads coverage to Codecov

2. **Publish**: Triggered when a tag is pushed
   - Builds the package with Poetry
   - Publishes to TestPyPI first
   - Publishes to PyPI

### How to Release New Versions

To release a new version:

1. Update the version in `pyproject.toml`
2. Commit changes and push
3. Create and push a new tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
4. GitHub Actions will automatically build and publish the package to PyPI

### Required Secrets

For the publishing workflow to work, you need to set up these GitHub repository secrets:

- `TEST_PYPI_API_TOKEN`: API token for TestPyPI
- `PYPI_API_TOKEN`: API token for PyPI

You can create these tokens on the respective websites (TestPyPI and PyPI) and add them to your repository's secrets in GitHub Settings.
