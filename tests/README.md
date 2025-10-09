# Testing Guide

This project uses pytest as the testing framework.

## Install Test Dependencies

```bash
pip install -r requirements.txt
```

## Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with extra verbosity
pytest -vv
```

## Run Specific Tests

```bash
# Run specific test file
pytest tests/test_main.py

# Run specific test class
pytest tests/test_main.py::TestRootEndpoint

# Run specific test function
pytest tests/test_main.py::TestRootEndpoint::test_root_endpoint

# Filter by keyword
pytest -k "health"
```

## Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # pytest configuration and shared fixtures
├── test_main.py         # API endpoints tests
├── test_schema.py       # Pydantic schema tests
└── test_utils.py        # Utility function tests
```

## Test Coverage

### test_main.py
- ✅ Root endpoint test (`/`)
- ✅ Health check test (`/health`)
- ✅ This week tournaments test (`/this-week-tournaments`)
  - Success case
  - Failure case
- ✅ Two days matches test (`/two-days-matches`)
  - Missing URL parameter
  - Invalid URL
  - Success case
  - Failure case

### test_schema.py
- ✅ TournamentRequest validation
- ✅ TournamentData validation
- ✅ ScrapeResponse validation
- ✅ TwoDaysResponse validation

### test_utils.py
- ✅ clear_directory function tests
  - Clear empty directory
  - Clear directory with files
  - Clear directory with subdirectories
  - Create non-existent directory

## Run Tests in Docker

### Method 1: Direct Execution (Recommended)

```bash
# Run tests in a new container (doesn't require running container)
docker compose run --rm badminton-api pytest

# Run with verbose output
docker compose run --rm badminton-api pytest -v

# Run specific test file
docker compose run --rm badminton-api pytest tests/test_main.py

# Run only failed tests
docker compose run --rm badminton-api pytest --lf
```

### Method 2: Enter Container Shell

```bash
# Start container (if not already running)
docker compose up -d

# Enter running container
docker compose exec badminton-api bash

# Run tests inside container
pytest
pytest -v
pytest tests/test_main.py

# Exit container
exit
```

### Method 3: Using docker exec

```bash
# Enter container (using container name)
docker exec -it badminton-scraper-api bash

# Run tests
pytest

# Exit
exit
```

## Writing New Tests

1. Create new test files in `tests/` directory, starting with `test_`
2. Test class names should start with `Test`
3. Test function names should start with `test_`
4. Use fixtures defined in `conftest.py`
5. Use mocks appropriately to isolate external dependencies

### Test Example

```python
import pytest
from unittest.mock import patch

def test_example(client):
    """Test example"""
    response = client.get("/endpoint")
    assert response.status_code == 200
    assert "expected_key" in response.json()

@patch('module.function')
def test_with_mock(mock_function, client):
    """Test example with mock"""
    mock_function.return_value = "mocked_value"
    response = client.get("/endpoint")
    assert response.status_code == 200
```

## Frequently Asked Questions

### Q: Test failed with module not found error
A: Make sure to run tests from the project root directory, or set PYTHONPATH:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
```

### Q: How to test async functions?
A: Use `pytest-asyncio`:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

### Q: How to run only failed tests?
A: Use `pytest --lf` (last failed) or `pytest --ff` (failed first) parameter
