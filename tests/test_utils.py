"""
Unit Tests for Shared Utilities

Tests for Bedrock invocation, DynamoDB operations, and helper functions.

References:
- 17_testing_strategy.md: Testing approach and coverage requirements
- 16_module_build_checklist.md: Phase 2 verification criteria

Verification Sources:
- pytest Documentation: https://docs.pytest.org/
- moto (AWS mocking): https://docs.getmoto.org/
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import functions to test
from shared.utils import (
    invoke_bedrock,
    save_to_dynamodb,
    get_from_dynamodb,
    update_dynamodb_item,
    generate_id,
    get_timestamp,
    format_error_response,
    format_success_response,
    validate_required_fields,
    truncate_text,
    calculate_percentage,
    track_agent_cost
)
from shared.config import Config


# ============================================================================
# Helper Function Tests
# ============================================================================

def test_generate_id():
    """Test ID generation"""
    # Test without prefix
    id1 = generate_id()
    id2 = generate_id()
    
    assert id1 != id2
    assert len(id1) == 36  # UUID4 length
    
    # Test with prefix
    prefixed_id = generate_id("test-")
    assert prefixed_id.startswith("test-")
    assert len(prefixed_id) == 41  # "test-" + UUID


def test_get_timestamp():
    """Test timestamp generation"""
    ts1 = get_timestamp()
    ts2 = get_timestamp()
    
    assert isinstance(ts1, int)
    assert isinstance(ts2, int)
    assert ts2 >= ts1  # Second timestamp should be >= first


def test_format_error_response():
    """Test error response formatting"""
    response = format_error_response(
        "Test error",
        context={"key": "value"},
        error_code="TEST_ERROR"
    )
    
    assert response['status'] == 'error'
    assert response['error'] == "Test error"
    assert response['error_code'] == "TEST_ERROR"
    assert response['context']['key'] == "value"
    assert 'timestamp' in response


def test_format_success_response():
    """Test success response formatting"""
    response = format_success_response(
        {"result": "data"},
        metadata={"meta": "info"}
    )
    
    assert response['status'] == 'success'
    assert response['data']['result'] == "data"
    assert response['metadata']['meta'] == "info"
    assert 'timestamp' in response


def test_validate_required_fields():
    """Test field validation"""
    # Test with all fields present
    data = {'name': 'John', 'email': 'john@example.com', 'phone': '123-456-7890'}
    error = validate_required_fields(data, ['name', 'email', 'phone'])
    assert error is None
    
    # Test with missing field
    data = {'name': 'John', 'email': 'john@example.com'}
    error = validate_required_fields(data, ['name', 'email', 'phone'])
    assert error is not None
    assert 'phone' in error
    
    # Test with empty field
    data = {'name': 'John', 'email': '', 'phone': '123-456-7890'}
    error = validate_required_fields(data, ['name', 'email', 'phone'])
    assert error is not None
    assert 'email' in error


def test_truncate_text():
    """Test text truncation"""
    # Test short text (no truncation)
    short_text = "Hello world"
    result = truncate_text(short_text, max_length=100)
    assert result == short_text
    
    # Test long text (truncation)
    long_text = "A" * 1000
    result = truncate_text(long_text, max_length=50)
    assert len(result) == 50
    assert result.endswith("...")
    
    # Test custom suffix
    result = truncate_text(long_text, max_length=50, suffix="[...]")
    assert result.endswith("[...]")


def test_calculate_percentage():
    """Test percentage calculation"""
    # Normal case
    assert calculate_percentage(25, 100) == 25.0
    assert calculate_percentage(50, 200) == 25.0
    
    # Edge case: division by zero
    assert calculate_percentage(10, 0) == 0.0
    
    # Edge case: part > total
    assert calculate_percentage(150, 100) == 150.0


# ============================================================================
# Bedrock Invocation Tests
# ============================================================================

@patch('shared.utils.bedrock_runtime')
def test_invoke_bedrock_success(mock_bedrock):
    """Test successful Bedrock invocation"""
    # Mock successful response
    mock_response = {
        'output': {
            'message': {
                'content': [{'text': 'Test response from Nova'}]
            }
        },
        'usage': {
            'inputTokens': 10,
            'outputTokens': 20
        }
    }
    mock_bedrock.converse.return_value = mock_response
    
    # Invoke Bedrock
    result = invoke_bedrock("Test prompt")
    
    # Verify result
    assert result['success'] is True
    assert result['content'] == 'Test response from Nova'
    assert result['input_tokens'] == 10
    assert result['output_tokens'] == 20
    assert 'cost_usd' in result
    assert 'latency' in result
    assert result['model_id'] == Config.BEDROCK_MODEL_ID
    
    # Verify Bedrock was called correctly
    mock_bedrock.converse.assert_called_once()
    call_args = mock_bedrock.converse.call_args
    assert call_args[1]['modelId'] == Config.BEDROCK_MODEL_ID


@patch('shared.utils.bedrock_runtime')
def test_invoke_bedrock_with_system_prompt(mock_bedrock):
    """Test Bedrock invocation with system prompt"""
    mock_response = {
        'output': {'message': {'content': [{'text': 'Response'}]}},
        'usage': {'inputTokens': 15, 'outputTokens': 25}
    }
    mock_bedrock.converse.return_value = mock_response
    
    result = invoke_bedrock(
        "User prompt",
        system_prompt="You are a helpful assistant"
    )
    
    assert result['success'] is True
    call_args = mock_bedrock.converse.call_args
    assert 'system' in call_args[1]


@patch('shared.utils.bedrock_runtime')
def test_invoke_bedrock_throttling_retry(mock_bedrock):
    """Test Bedrock throttling with retry"""
    from botocore.exceptions import ClientError
    
    # First call fails with throttling, second succeeds
    mock_bedrock.converse.side_effect = [
        ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
            'converse'
        ),
        {
            'output': {'message': {'content': [{'text': 'Success after retry'}]}},
            'usage': {'inputTokens': 10, 'outputTokens': 20}
        }
    ]
    
    result = invoke_bedrock("Test prompt")
    
    # Should succeed after retry
    assert result['success'] is True
    assert result['content'] == 'Success after retry'
    assert mock_bedrock.converse.call_count == 2


@patch('shared.utils.bedrock_runtime')
def test_invoke_bedrock_error(mock_bedrock):
    """Test Bedrock invocation error handling"""
    from botocore.exceptions import ClientError
    
    # Mock error response
    mock_bedrock.converse.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'Invalid input'}},
        'converse'
    )
    
    result = invoke_bedrock("Test prompt")
    
    # Should return error
    assert result['success'] is False
    assert 'error' in result
    assert result['error_code'] == 'ValidationException'


# ============================================================================
# DynamoDB Operation Tests
# ============================================================================

@patch('shared.utils.dynamodb')
def test_save_to_dynamodb_success(mock_dynamodb):
    """Test successful DynamoDB save"""
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    item = {'candidateId': 'cand-123', 'name': 'John Doe'}
    result = save_to_dynamodb('talent-acq-candidates', item)
    
    assert result['success'] is True
    mock_table.put_item.assert_called_once_with(Item=item)


@patch('shared.utils.dynamodb')
def test_save_to_dynamodb_error(mock_dynamodb):
    """Test DynamoDB save error handling"""
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
        'put_item'
    )
    mock_dynamodb.Table.return_value = mock_table
    
    result = save_to_dynamodb('nonexistent-table', {})
    
    assert result['success'] is False
    assert 'error' in result
    assert result['error_code'] == 'ResourceNotFoundException'


@patch('shared.utils.dynamodb')
def test_get_from_dynamodb_success(mock_dynamodb):
    """Test successful DynamoDB get"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        'Item': {'candidateId': 'cand-123', 'name': 'John Doe'}
    }
    mock_dynamodb.Table.return_value = mock_table
    
    item = get_from_dynamodb('talent-acq-candidates', {'candidateId': 'cand-123'})
    
    assert item is not None
    assert item['candidateId'] == 'cand-123'
    assert item['name'] == 'John Doe'


@patch('shared.utils.dynamodb')
def test_get_from_dynamodb_not_found(mock_dynamodb):
    """Test DynamoDB get when item not found"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}  # No 'Item' key
    mock_dynamodb.Table.return_value = mock_table
    
    item = get_from_dynamodb('talent-acq-candidates', {'candidateId': 'nonexistent'})
    
    assert item is None


@patch('shared.utils.dynamodb')
def test_update_dynamodb_item_success(mock_dynamodb):
    """Test successful DynamoDB update"""
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    result = update_dynamodb_item(
        'talent-acq-candidates',
        {'candidateId': 'cand-123'},
        {'status': 'screened', 'screeningScore': 0.85}
    )
    
    assert result['success'] is True
    mock_table.update_item.assert_called_once()


# ============================================================================
# Cost Tracking Tests
# ============================================================================

def test_config_calculate_cost():
    """Test cost calculation"""
    # Test with known values
    input_tokens = 1000
    output_tokens = 500
    
    cost = Config.calculate_cost(input_tokens, output_tokens)
    
    # Expected: (1000/1000 * 0.00006) + (500/1000 * 0.00024)
    # = 0.00006 + 0.00012 = 0.00018
    expected_cost = 0.00018
    assert abs(cost - expected_cost) < 0.0000001  # Float comparison with tolerance


@patch('shared.utils.update_dynamodb_item')
def test_track_agent_cost(mock_update):
    """Test agent cost tracking"""
    mock_update.return_value = {'success': True}
    
    result = track_agent_cost(
        agent_name='sourcing',
        input_tokens=1000,
        output_tokens=500,
        state_id='state-123'
    )
    
    assert result['agent_name'] == 'sourcing'
    assert result['input_tokens'] == 1000
    assert result['output_tokens'] == 500
    assert 'cost_usd' in result
    
    # Verify DynamoDB update was called
    mock_update.assert_called_once()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
