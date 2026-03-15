"""
Pytest Configuration and Shared Fixtures

This file contains shared fixtures and configuration for all tests.
Fixtures defined here are automatically available to all test files.

References:
- pytest documentation: https://docs.pytest.org/en/stable/fixture.html
- 17_testing_strategy.md: Testing approach and patterns
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import pytz


# ============================================================================
# AWS Service Mocks
# ============================================================================

@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock runtime client"""
    mock_client = MagicMock()
    mock_client.converse.return_value = {
        'output': {
            'message': {
                'content': [{'text': 'Mock response from Nova'}]
            }
        },
        'usage': {
            'inputTokens': 100,
            'outputTokens': 50
        }
    }
    return mock_client


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB client"""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.Table.return_value = mock_table
    return mock_client


@pytest.fixture
def mock_lambda_client():
    """Mock Lambda client"""
    mock_client = MagicMock()
    mock_client.invoke.return_value = {
        'StatusCode': 200,
        'Payload': MagicMock(read=lambda: json.dumps({
            'statusCode': 200,
            'body': json.dumps({'status': 'success', 'data': {}})
        }).encode())
    }
    return mock_client


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job():
    """Sample job posting data"""
    return {
        'jobId': 'job-test-001',
        'title': 'Senior Software Engineer',
        'company': 'TechCorp',
        'description': 'Build scalable cloud systems using Python and AWS',
        'location': 'Seattle, WA',
        'remote_allowed': True,
        'requirements': {
            'required_skills': ['Python', 'AWS', 'React'],
            'preferred_skills': ['Docker', 'Kubernetes'],
            'experience_years': {'min': 5, 'max': 10},
            'education': 'Bachelor\'s in Computer Science'
        },
        'salary_range': {'min': 140000, 'max': 180000},
        'status': 'open',
        'createdAt': 1710432000,
        'updatedAt': 1710432000
    }


@pytest.fixture
def sample_candidate():
    """Sample candidate data"""
    return {
        'candidate_id': 'cand-001',
        'name': 'Alice Johnson',
        'email': 'alice@example.com',
        'current_title': 'Software Engineer',
        'current_company': 'CloudTech Inc',
        'location': 'Seattle, WA',
        'skills': ['Python', 'AWS', 'React', 'Docker'],
        'experience_years': 7,
        'education': 'BS Computer Science, MIT',
        'linkedin_url': 'https://linkedin.com/in/alice',
        'github_url': 'https://github.com/alice',
        'screening_score': 0.92,
        'strengths': [
            'Python expert with 7 years experience',
            'AWS certified solutions architect',
            'Strong React and frontend skills'
        ]
    }


@pytest.fixture
def sample_candidates(sample_candidate):
    """List of sample candidates"""
    return [
        sample_candidate,
        {
            'candidate_id': 'cand-002',
            'name': 'Bob Smith',
            'email': 'bob@example.com',
            'current_title': 'Backend Developer',
            'current_company': 'DataCorp',
            'location': 'Remote',
            'skills': ['Python', 'AWS', 'PostgreSQL'],
            'experience_years': 5,
            'education': 'BS Computer Science',
            'screening_score': 0.85,
            'strengths': [
                'Python backend specialist',
                'AWS infrastructure expert'
            ]
        },
        {
            'candidate_id': 'cand-003',
            'name': 'Carol Williams',
            'email': 'carol@example.com',
            'current_title': 'Full Stack Engineer',
            'current_company': 'StartupXYZ',
            'location': 'San Francisco, CA',
            'skills': ['Python', 'React', 'Node.js'],
            'experience_years': 6,
            'education': 'MS Computer Science',
            'screening_score': 0.88,
            'strengths': [
                'Full-stack expertise',
                'Startup experience'
            ]
        }
    ]


@pytest.fixture
def sample_agent_state():
    """Sample agent state for workflow testing"""
    return {
        'stateId': 'state-test-001',
        'jobId': 'job-test-001',
        'currentAgent': None,
        'workflowStatus': 'initialized',
        'agentsExecuted': [],
        'currentStep': 0,
        'totalSteps': 5,
        'sharedContext': {'job_id': 'job-test-001'},
        'agentResults': {},
        'errors': [],
        'totalInputTokens': 0,
        'totalOutputTokens': 0,
        'totalCostUsd': 0.0,
        'createdAt': 1710432000,
        'updatedAt': 1710432000
    }


@pytest.fixture
def sample_interviewer_feedback():
    """Sample interviewer feedback"""
    return [
        {
            'interviewer_name': 'Jane Smith',
            'interviewer_role': 'Senior Engineer',
            'scores': {
                'technical_skills': 4.5,
                'problem_solving': 4.0,
                'communication': 5.0,
                'cultural_fit': 4.5,
                'leadership_potential': 4.0
            },
            'comments': 'Strong technical skills, excellent communication.',
            'recommendation': 'strong_yes',
            'confidence': 0.9
        },
        {
            'interviewer_name': 'John Doe',
            'interviewer_role': 'Tech Lead',
            'scores': {
                'technical_skills': 4.0,
                'problem_solving': 4.5,
                'communication': 4.5,
                'cultural_fit': 4.0,
                'leadership_potential': 4.5
            },
            'comments': 'Excellent problem-solving approach.',
            'recommendation': 'strong_yes',
            'confidence': 0.85
        }
    ]


# ============================================================================
# Nova Response Mocks
# ============================================================================

@pytest.fixture
def mock_nova_success_response():
    """Mock successful Nova API response"""
    return {
        'success': True,
        'content': 'This is a mock response from Amazon Nova',
        'input_tokens': 100,
        'output_tokens': 50,
        'cost_usd': 0.00001,
        'latency': 1.5,
        'model_id': 'amazon.nova-lite-v1:0'
    }


@pytest.fixture
def mock_nova_json_response():
    """Mock Nova response with JSON content"""
    return {
        'success': True,
        'content': json.dumps({
            'result': 'success',
            'data': {'key': 'value'}
        }),
        'input_tokens': 120,
        'output_tokens': 60,
        'cost_usd': 0.000012,
        'latency': 1.8,
        'model_id': 'amazon.nova-lite-v1:0'
    }


@pytest.fixture
def mock_nova_error_response():
    """Mock Nova error response"""
    return {
        'success': False,
        'error': 'ThrottlingException: Rate limit exceeded',
        'error_code': 'ThrottlingException'
    }


# ============================================================================
# Time and Date Fixtures
# ============================================================================

@pytest.fixture
def fixed_datetime():
    """Fixed datetime for consistent testing"""
    return datetime(2026, 3, 20, 14, 0, 0, tzinfo=pytz.UTC)


@pytest.fixture
def date_range():
    """Date range for testing"""
    start = datetime(2026, 3, 20, tzinfo=pytz.UTC)
    return {
        'start': start,
        'end': start + timedelta(days=7),
        'dates': [start + timedelta(days=i) for i in range(7)]
    }


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "aws: mark test as requiring AWS services"
    )


# ============================================================================
# Test Helpers
# ============================================================================

@pytest.fixture
def assert_valid_response():
    """Helper to assert valid API response structure"""
    def _assert(response):
        assert 'status' in response
        assert response['status'] in ['success', 'error']
        if response['status'] == 'success':
            assert 'data' in response
        else:
            assert 'error' in response
            assert 'error_code' in response
    return _assert


@pytest.fixture
def assert_valid_agent_result():
    """Helper to assert valid agent result structure"""
    def _assert(result):
        assert 'status' in result
        assert 'agent_name' in result or 'data' in result
        if result['status'] == 'success':
            assert 'data' in result
            assert 'metadata' in result or 'timestamp' in result
    return _assert
