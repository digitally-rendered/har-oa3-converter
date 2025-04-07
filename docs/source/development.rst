Development Guide
===============

This guide provides information for developers who want to contribute to the HAR to OpenAPI 3 Converter project.

Setup Development Environment
--------------------------

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/digitally-rendered/har-oa3-converter.git
       cd har-oa3-converter

2. Install dependencies with Poetry:

   .. code-block:: bash

       poetry install

3. Activate the virtual environment:

   .. code-block:: bash

       poetry shell

Code Quality
-----------

The project adheres to strict code quality standards, using multiple tools:

- **Black**: For consistent code formatting
- **Pylint**: For static code analysis
- **mypy**: For type checking

Run these tools before submitting any changes:

.. code-block:: bash

    # Format code
    poetry run black har_oa3_converter tests

    # Sort imports
    poetry run isort har_oa3_converter tests

    # Check with pylint
    poetry run pylint har_oa3_converter

    # Run type checking
    poetry run mypy har_oa3_converter

Testing
-------

The project maintains **100% test coverage** as a requirement. All code changes must include corresponding tests.

Running Tests
^^^^^^^^^^^^

.. code-block:: bash

    # Run all tests
    poetry run pytest

    # Run with coverage report
    poetry run pytest --cov=har_oa3_converter --cov-report=term-missing

    # Generate HTML coverage report
    poetry run pytest --cov=har_oa3_converter --cov-report=html

    # Generate JSON report
    poetry run pytest --json-report

    # Run tests in parallel
    poetry run pytest -xvs -n auto

All of these testing commands can be combined to produce various report formats simultaneously:

.. code-block:: bash

    poetry run pytest --cov=har_oa3_converter --cov-report=xml --cov-report=html --cov-report=term --html=pytest-report.html --json-report --json-report-file=pytest-report.json --cov-branch -v

Test Organization
^^^^^^^^^^^^^^^

Tests are organized in the following structure:

- ``tests/``: Root test directory
  - ``cli/``: Tests for command-line interfaces
  - ``converters/``: Tests for format converters
  - ``utils/``: Tests for utility functions
  - ``api/``: Tests for the REST API
  - ``models/``: Tests for data models

JSON Schema Validation in Tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All models must be represented in JSON_SCHEMA documents and thoroughly tested:

.. code-block:: python

    def test_model_schema_validation():
        # Create test data
        test_data = {...}

        # Validate against schema
        from har_oa3_converter.converters.schema_validator import validate_schema
        validation_result = validate_schema(test_data, schema="model_schema")

        # Assert validation success
        assert validation_result.is_valid

Multi-environment Testing
^^^^^^^^^^^^^^^^^^^^^^^

The project uses tox for testing across multiple Python versions (3.8, 3.9, 3.10, 3.11):

.. code-block:: bash

    # Run tests on all supported Python versions
    tox

    # Run on a specific version
    tox -e py310

Documentation
------------

Build the documentation:

.. code-block:: bash

    cd docs
    poetry run sphinx-build -b html source build

The documentation will be available in the ``docs/build`` directory.

Release Process
------------

1. Update version in ``pyproject.toml``
2. Update the changelog
3. Commit changes
4. Create a tag for the new version
5. Push tag to GitHub
6. The CI/CD pipeline will automatically build and publish to PyPI

.. code-block:: bash

    # Update version
    poetry version patch  # or minor or major

    # Commit changes
    git add pyproject.toml CHANGELOG.md
    git commit -m "Release version $(poetry version -s)"

    # Create and push tag
    git tag v$(poetry version -s)
    git push origin main v$(poetry version -s)
