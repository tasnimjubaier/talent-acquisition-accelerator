# Tests Directory

Unit and integration tests for all components.

## Structure

- `test_utils.py` - Tests for shared utilities
- `test_agents/` - Tests for individual agents
- `test_integration/` - End-to-end integration tests

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py -v
```

## Status

🚧 Tests being added incrementally with each component
