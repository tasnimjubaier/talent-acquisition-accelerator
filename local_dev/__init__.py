"""
Local Development Environment for Talent Acquisition Accelerator

This package provides mock AWS services for local testing without costs:
- mock_bedrock: Simulates Amazon Bedrock Nova API
- mock_dynamodb: In-memory DynamoDB implementation
- mock_lambda: Local Lambda function invocation
- local_runner: Complete workflow orchestration

Quick Start:
    python local_dev/local_runner.py --job-file demo/01_sample_jobs.json --job-index 0

See README.md for detailed documentation.
"""

__version__ = '1.0.0'
__all__ = [
    'mock_bedrock',
    'mock_dynamodb',
    'mock_lambda',
    'local_runner'
]
