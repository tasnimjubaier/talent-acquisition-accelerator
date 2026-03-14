"""
Unit Tests for Supervisor Agent

Tests the SupervisorAgent class methods including workflow initialization,
agent routing, result recording, task decomposition, and error handling.

References:
- 16_module_build_checklist.md: Phase 3 testing requirements
- 17_testing_strategy.md: Testing approach and patterns

Verification Sources:
- Pytest Documentation: https://docs.pytest.org/
- Mocking AWS Services: https://docs.getmoto.org/
- Python Unit Testing Best Practices: https://realpython.com/python-testing/
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the supervisor agent
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.supervisor_agent import SupervisorAgent, lambda_handler
from shared.models import AgentState, Job


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def supervisor():
    """Create a SupervisorAgent instance for testing"""
    return SupervisorAgent()


@pytest.fixture
def mock_job():
    """Create a mock job for testing"""
    return {
        'jobId': 'job-test-123',
        'title': 'Senior Software Engineer',
        'description': 'Looking for an experienced Python developer',
        'requirements': {
            'skills': ['Python', 'AWS', 'DynamoDB'],
            'experience_years': 5,
            'location': 'Remote'
        },
        'status': 'open',
        'createdAt': 1710432000
    }


@pytest.fixture
def mock_agent_state():
    """Create a mock agent state for testing"""
    return {
        'stateId': 'state-test-456',
        'jobId': 'job-test-123',
        'currentAgent': None,
        'workflowStatus': 'initialized',
        'agentsExecuted': [],
        'currentStep': 0,
        'totalSteps': 5,
        'sharedContext': {'job_id': 'job-test-123'},
        'agentResults': {},
        'errors': [],
        'totalInputTokens': 0,
        'totalOutputTokens': 0,
        'totalCostUsd': 0.0,
        'createdAt': 1710432000,
        'updatedAt': 1710432000
    }


# ============================================================================
# Test: Supervisor Initialization
# ============================================================================

def test_supervisor_initialization(supervisor):
    """Test that SupervisorAgent initializes correctly"""
    assert supervisor.agent_name == "SupervisorAgent"
    assert len(supervisor.agent_pipeline) == 5
    assert supervisor.agent_pipeline[0] == "SourcingAgent"
    assert supervisor.agent_pipeline[4] == "EvaluationAgent"


# ============================================================================
# Test: Start Workflow
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.save_to_dynamodb')
def test_start_workflow_success(mock_save, mock_get, supervisor, mock_job):
    """Test successful workflow initialization"""
    # Mock DynamoDB responses
    mock_get.return_value = mock_job
    mock_save.return_value = {'success': True}
    
    # Start workflow
    result = supervisor.start_workflow('job-test-123')
    
    # Verify result
    assert result['status'] == 'success'
    assert result['data']['job_id'] == 'job-test-123'
    assert result['data']['workflow_status'] == 'initialized'
    assert result['data']['next_agent'] == 'SourcingAgent'
    assert 'state_id' in result['data']
    
    # Verify DynamoDB calls
    mock_get.assert_called_once()
    mock_save.assert_called_once()


@patch('agents.supervisor_agent.get_from_dynamodb')
def test_start_workflow_job_not_found(mock_get, supervisor):
    """Test workflow start with non-existent job"""
    # Mock job not found
    mock_get.return_value = None
    
    # Start workflow
    result = supervisor.start_workflow('job-nonexistent')
    
    # Verify error response
    assert result['status'] == 'error'
    assert 'not found' in result['error'].lower()
    assert result['error_code'] == 'JobNotFound'



@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.save_to_dynamodb')
def test_start_workflow_with_config(mock_save, mock_get, supervisor, mock_job):
    """Test workflow start with custom configuration"""
    mock_get.return_value = mock_job
    mock_save.return_value = {'success': True}
    
    config = {'target_candidates': 100, 'sourcing_strategy': 'aggressive'}
    result = supervisor.start_workflow('job-test-123', workflow_config=config)
    
    assert result['status'] == 'success'
    assert result['data']['workflow_status'] == 'initialized'


# ============================================================================
# Test: Execute Next Step
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_execute_next_step_first_agent(mock_update, mock_get, supervisor, mock_agent_state):
    """Test executing the first agent in pipeline"""
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    result = supervisor.execute_next_step('state-test-456')
    
    assert result['status'] == 'success'
    assert result['data']['next_agent'] == 'SourcingAgent'
    assert result['data']['current_step'] == 1
    assert result['data']['total_steps'] == 5


@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_execute_next_step_middle_agent(mock_update, mock_get, supervisor, mock_agent_state):
    """Test executing a middle agent in pipeline"""
    # Simulate workflow at step 2
    mock_agent_state['currentStep'] = 2
    mock_agent_state['agentsExecuted'] = ['SourcingAgent', 'ScreeningAgent']
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    result = supervisor.execute_next_step('state-test-456')
    
    assert result['status'] == 'success'
    assert result['data']['next_agent'] == 'OutreachAgent'
    assert result['data']['current_step'] == 3


@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_execute_next_step_workflow_complete(mock_update, mock_get, supervisor, mock_agent_state):
    """Test executing next step when all agents are done"""
    # Simulate completed workflow
    mock_agent_state['currentStep'] = 5
    mock_agent_state['agentsExecuted'] = [
        'SourcingAgent', 'ScreeningAgent', 'OutreachAgent',
        'SchedulingAgent', 'EvaluationAgent'
    ]
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    result = supervisor.execute_next_step('state-test-456')
    
    assert result['status'] == 'success'
    assert result['data']['workflow_status'] == 'completed'
    assert 'All agents executed' in result['data']['message']


@patch('agents.supervisor_agent.get_from_dynamodb')
def test_execute_next_step_state_not_found(mock_get, supervisor):
    """Test execute next step with non-existent state"""
    mock_get.return_value = None
    
    result = supervisor.execute_next_step('state-nonexistent')
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'StateNotFound'


# ============================================================================
# Test: Record Agent Result
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_record_agent_result_success(mock_update, mock_get, supervisor, mock_agent_state):
    """Test recording agent result successfully"""
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    agent_result = {
        'candidates_found': 50,
        'top_candidates': 10
    }
    
    result = supervisor.record_agent_result(
        state_id='state-test-456',
        agent_name='SourcingAgent',
        result=agent_result,
        input_tokens=1000,
        output_tokens=500
    )
    
    assert result['status'] == 'success'
    assert result['data']['agent_name'] == 'SourcingAgent'
    assert result['data']['agents_completed'] == 1
    assert 'total_cost_usd' in result['data']



@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_record_agent_result_cost_tracking(mock_update, mock_get, supervisor, mock_agent_state):
    """Test that cost tracking accumulates correctly"""
    # First agent execution
    mock_agent_state['totalInputTokens'] = 500
    mock_agent_state['totalOutputTokens'] = 300
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    result = supervisor.record_agent_result(
        state_id='state-test-456',
        agent_name='ScreeningAgent',
        result={'screened': 25},
        input_tokens=800,
        output_tokens=400
    )
    
    assert result['status'] == 'success'
    # Verify cost is calculated (should be > 0)
    assert result['data']['total_cost_usd'] > 0


# ============================================================================
# Test: Decompose Task
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.invoke_bedrock')
def test_decompose_task_success(mock_bedrock, mock_get, supervisor, mock_job):
    """Test task decomposition with valid Nova response"""
    mock_get.return_value = mock_job
    
    # Mock Nova response with valid JSON
    mock_bedrock.return_value = {
        'success': True,
        'content': json.dumps({
            'sourcing': {'target_count': 50, 'sources': ['linkedin', 'github']},
            'screening': {'evaluation_criteria': ['Python', 'AWS'], 'pass_threshold': 0.7},
            'outreach': {'message_tone': 'professional', 'channels': ['email']},
            'scheduling': {'interview_type': 'technical', 'duration_minutes': 60},
            'evaluation': {'focus_areas': ['technical_skills', 'experience']}
        }),
        'input_tokens': 500,
        'output_tokens': 300,
        'cost_usd': 0.0012
    }
    
    result = supervisor.decompose_task(
        'job-test-123',
        'Find and screen 50 Python developers'
    )
    
    assert result['status'] == 'success'
    assert 'task_breakdown' in result['data']
    assert 'sourcing' in result['data']['task_breakdown']
    assert result['data']['task_breakdown']['sourcing']['target_count'] == 50


@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.invoke_bedrock')
def test_decompose_task_invalid_json(mock_bedrock, mock_get, supervisor, mock_job):
    """Test task decomposition when Nova returns invalid JSON"""
    mock_get.return_value = mock_job
    
    # Mock Nova response with invalid JSON
    mock_bedrock.return_value = {
        'success': True,
        'content': 'This is not valid JSON',
        'input_tokens': 500,
        'output_tokens': 100,
        'cost_usd': 0.0008
    }
    
    result = supervisor.decompose_task(
        'job-test-123',
        'Find candidates'
    )
    
    # Should still succeed with default breakdown
    assert result['status'] == 'success'
    assert 'task_breakdown' in result['data']


@patch('agents.supervisor_agent.get_from_dynamodb')
def test_decompose_task_job_not_found(mock_get, supervisor):
    """Test task decomposition with non-existent job"""
    mock_get.return_value = None
    
    result = supervisor.decompose_task('job-nonexistent', 'Find candidates')
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'JobNotFound'


# ============================================================================
# Test: Aggregate Results
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.invoke_bedrock')
def test_aggregate_results_success(mock_bedrock, mock_get, supervisor, mock_agent_state):
    """Test result aggregation with valid Nova response"""
    # Add agent results to state
    mock_agent_state['agentResults'] = {
        'SourcingAgent': {'result': {'candidates_found': 50}},
        'ScreeningAgent': {'result': {'candidates_screened': 25}},
        'OutreachAgent': {'result': {'messages_sent': 25}}
    }
    mock_get.return_value = mock_agent_state
    
    # Mock Nova aggregation response
    mock_bedrock.return_value = {
        'success': True,
        'content': json.dumps({
            'executive_summary': 'Successfully processed 50 candidates',
            'key_metrics': {
                'candidates_sourced': 50,
                'candidates_screened': 25,
                'candidates_contacted': 25
            },
            'highlights': ['Strong candidate pool', 'High response rate'],
            'concerns': [],
            'recommendations': ['Schedule interviews quickly']
        }),
        'input_tokens': 800,
        'output_tokens': 400,
        'cost_usd': 0.0015
    }
    
    result = supervisor.aggregate_results('state-test-456')
    
    assert result['status'] == 'success'
    assert 'summary' in result['data']
    assert 'executive_summary' in result['data']['summary']



@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.invoke_bedrock')
def test_aggregate_results_nova_failure(mock_bedrock, mock_get, supervisor, mock_agent_state):
    """Test result aggregation when Nova fails"""
    mock_agent_state['agentResults'] = {
        'SourcingAgent': {'result': {'candidates_found': 50}}
    }
    mock_get.return_value = mock_agent_state
    
    # Mock Nova failure
    mock_bedrock.return_value = {
        'success': False,
        'error': 'API timeout'
    }
    
    result = supervisor.aggregate_results('state-test-456')
    
    # Should still return success with raw results
    assert result['status'] == 'success'
    assert 'agent_results' in result['data']


# ============================================================================
# Test: Handle Error
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_handle_error_success(mock_update, mock_get, supervisor, mock_agent_state):
    """Test error handling records error correctly"""
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    result = supervisor.handle_error(
        state_id='state-test-456',
        agent_name='SourcingAgent',
        error='API timeout',
        error_context={'retry_count': 3}
    )
    
    assert result['status'] == 'error'
    assert 'SourcingAgent' in result['error']
    assert result['error_code'] == 'AgentExecutionFailed'


@patch('agents.supervisor_agent.get_from_dynamodb')
@patch('agents.supervisor_agent.update_dynamodb_item')
def test_handle_error_multiple_errors(mock_update, mock_get, supervisor, mock_agent_state):
    """Test handling multiple errors accumulates them"""
    # Add existing error
    mock_agent_state['errors'] = [
        {'agent_name': 'SourcingAgent', 'error': 'First error'}
    ]
    mock_get.return_value = mock_agent_state
    mock_update.return_value = {'success': True}
    
    result = supervisor.handle_error(
        state_id='state-test-456',
        agent_name='ScreeningAgent',
        error='Second error'
    )
    
    assert result['status'] == 'error'
    assert result['context']['error_count'] == 2


# ============================================================================
# Test: Get Workflow Status
# ============================================================================

@patch('agents.supervisor_agent.get_from_dynamodb')
def test_get_workflow_status_success(mock_get, supervisor, mock_agent_state):
    """Test getting workflow status"""
    mock_agent_state['currentStep'] = 2
    mock_agent_state['agentsExecuted'] = ['SourcingAgent', 'ScreeningAgent']
    mock_get.return_value = mock_agent_state
    
    result = supervisor.get_workflow_status('state-test-456')
    
    assert result['status'] == 'success'
    assert result['data']['current_step'] == 2
    assert result['data']['total_steps'] == 5
    assert result['data']['progress_percentage'] == 40.0
    assert len(result['data']['agents_executed']) == 2


@patch('agents.supervisor_agent.get_from_dynamodb')
def test_get_workflow_status_not_found(mock_get, supervisor):
    """Test getting status for non-existent workflow"""
    mock_get.return_value = None
    
    result = supervisor.get_workflow_status('state-nonexistent')
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'StateNotFound'


# ============================================================================
# Test: Lambda Handler
# ============================================================================

@patch('agents.supervisor_agent.SupervisorAgent')
def test_lambda_handler_start_workflow(mock_supervisor_class):
    """Test Lambda handler for start_workflow operation"""
    mock_supervisor = Mock()
    mock_supervisor.start_workflow.return_value = {
        'status': 'success',
        'data': {'state_id': 'state-123'}
    }
    mock_supervisor_class.return_value = mock_supervisor
    
    event = {
        'operation': 'start_workflow',
        'job_id': 'job-123'
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'
    mock_supervisor.start_workflow.assert_called_once_with(
        job_id='job-123',
        workflow_config=None
    )


@patch('agents.supervisor_agent.SupervisorAgent')
def test_lambda_handler_unknown_operation(mock_supervisor_class):
    """Test Lambda handler with unknown operation"""
    mock_supervisor_class.return_value = Mock()
    
    event = {
        'operation': 'unknown_operation'
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'UnknownOperation'


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=agents.supervisor_agent', '--cov-report=term-missing'])
