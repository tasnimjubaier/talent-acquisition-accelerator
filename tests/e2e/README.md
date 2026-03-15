# End-to-End Tests

This directory contains end-to-end tests for the Talent Acquisition Accelerator system.

## Test Files

- `test_complete_workflow.py` - Complete recruiting pipeline tests
- `test_demo_scenarios.py` - Demo-specific scenario validation
- `test_performance_validation.py` - Performance and cost validation

## Running Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v -m e2e

# Run demo tests only
pytest tests/e2e/test_demo_scenarios.py -v -m demo

# Run performance tests
pytest tests/e2e/test_performance_validation.py -v -m performance

# Run with coverage
pytest tests/e2e/ --cov=agents --cov-report=html
```

## Test Markers

- `@pytest.mark.e2e` - End-to-end tests (slow, uses real APIs)
- `@pytest.mark.demo` - Demo scenario tests
- `@pytest.mark.performance` - Performance validation tests

## Requirements

These tests require:
- AWS credentials configured
- DynamoDB tables created
- Bedrock/Nova access enabled
- All agents deployed

## Expected Duration

- Complete workflow tests: 2-5 minutes per test
- Demo scenario tests: 1-3 minutes per test
- Performance tests: 1-2 minutes per test
