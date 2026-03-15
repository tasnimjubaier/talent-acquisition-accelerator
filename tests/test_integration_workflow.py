"""
Integration Tests for End-to-End Workflow

Tests the complete recruiting workflow from job posting through evaluation.
Verifies that all agents coordinate correctly and data flows properly.

Reference: 16_module_build_checklist.md - Phase 5, Step 5.4
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.supervisor_agent import SupervisorAgent, lambda_handler
from shared.models import AgentState, Job


class TestIntegrationWorkflow:
    """Test end-to-end workflow integration"""
    
    @pytest.fixture
    def supervisor(self):
        """Create supervisor agent instance"""
        return SupervisorAgent()
    
    @pytest.fixture
    def mock_job_data(self):
        """Mock job data for testing"""
        return {
            'jobId': 'test-job-001',
            'title': 'Senior Software Engineer',
            'description': 'Looking for experienced Python developer',
            'requirements': {
                'skills': ['Python', 'AWS', 'Docker'],
                'experience_years': 5,
                'location': 'Remote'
            },
            'status': 'open'
        }
    
    @pytest.fixture
    def mock_candidates(self):
        """Mock candidate data"""
        return [
            {
                'candidate_id': 'cand-001',
                'name': 'Alice Johnson',
                'email': 'alice@example.com',
                'skills': ['Python', 'AWS', 'Docker', 'Kubernetes'],
                'experience_years': 6,
                'location': 'Remote'
            },
            {
                'candidate_id': 'cand-002',
                'name': 'Bob Smith',
                'email': 'bob@example.com',
                'skills': ['Python', 'Django', 'PostgreSQL'],
                'experience_years': 4,
                'location': 'New York'
            }
        ]
    
    @patch('agents.supervisor_agent.get_from_dynamodb')
    @patch('agents.supervisor_agent.save_to_dynamodb')
    def test_workflow_initialization(self, mock_save, mock_get, supervisor, mock_job_data):
        """Test workflow initialization"""
        # Mock DynamoDB responses
        mock_get.return_value = mock_job_data
        mock_save.return_value = {'success': True}
        
        # Start workflow
        result = supervisor.start_workflow('test-job-001')
        
        # Verify success
        assert result['status'] == 'success'
        assert 'state_id' in result['data']
        assert result['data']['workflow_status'] == 'initialized'
        assert result['data']['next_agent'] == 'SourcingAgent'
        
        # Verify DynamoDB calls
        mock_get.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('agents.supervisor_agent.lambda_client')
    @patch('agents.supervisor_agent.get_from_dynamodb')
    @patch('agents.supervisor_agent.save_to_dynamodb')
    def test_agent_invocation(self, mock_save, mock_get, mock_lambda, supervisor, mock_candidates):
        """Test supervisor invoking worker agent"""
        # Mock Lambda response
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'data': {
                        'candidates': mock_candidates,
                        'summary': {'total_found': 2}
                    }
                })
            }).encode())
        }
        
        # Mock state retrieval
        mock_get.return_value = {
            'stateId': 'state-123',
            'jobId': 'test-job-001',
            'currentAgent': None,
            'workflowStatus': 'initialized'
        }
        mock_save.return_value = {'success': True}
        
        # Invoke agent
        payload = {
            'job_id': 'test-job-001',
            'parameters': {'target_count': 50}
        }
        result = supervisor._invoke_agent('sourcing', payload)
        
        # Verify invocation
        assert result['status'] == 'success'
        assert 'candidates' in result['data']
        assert len(result['data']['candidates']) == 2
        mock_lambda.invoke.assert_called_once()
    
    @patch('agents.supervisor_agent.lambda_client')
    @patch('agents.supervisor_agent.get_from_dynamodb')
    @patch('agents.supervisor_agent.save_to_dynamodb')
    @patch('agents.supervisor_agent.update_dynamodb_item')
    def test_sequential_workflow_execution(
        self, mock_update, mock_save, mock_get, mock_lambda, 
        supervisor, mock_job_data, mock_candidates
    ):
        """Test sequential execution of multiple agents"""
        # Mock workflow state
        workflow_state = {
            'workflow_id': 'workflow-123',
            'job_id': 'test-job-001',
            'status': 'in_progress',
            'completed_tasks': [],
            'tasks': [
                {
                    'agent': 'sourcing',
                    'parameters': {'target_count': 50},
                    'depends_on': None
                },
                {
                    'agent': 'screening',
                    'parameters': {'min_score': 0.7},
                    'depends_on': 'sourcing'
                }
            ]
        }
        
        # Mock Lambda responses for each agent
        def mock_invoke_side_effect(*args, **kwargs):
            function_name = kwargs.get('FunctionName', '')
            
            if 'sourcing' in function_name:
                response_data = {
                    'status': 'success',
                    'data': {
                        'candidates': mock_candidates,
                        'summary': {'total_found': 2}
                    }
                }
            elif 'screening' in function_name:
                response_data = {
                    'status': 'success',
                    'data': {
                        'qualified_candidates': [mock_candidates[0]],
                        'summary': {'qualified': 1, 'rejected': 1}
                    }
                }
            else:
                response_data = {'status': 'success', 'data': {}}
            
            return {
                'StatusCode': 200,
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps(response_data)
                }).encode())
            }
        
        mock_lambda.invoke.side_effect = mock_invoke_side_effect
        mock_get.return_value = mock_job_data
        mock_save.return_value = {'success': True}
        mock_update.return_value = {'success': True}
        
        # Execute workflow
        result = supervisor._execute_workflow(workflow_state)
        
        # Verify workflow completion
        assert result['status'] == 'completed'
        assert len(result['results']) == 2
        assert result['results'][0]['status'] == 'success'
        assert result['results'][1]['status'] == 'success'
        
        # Verify Lambda was called twice
        assert mock_lambda.invoke.call_count == 2
    
    @patch('agents.supervisor_agent.lambda_client')
    def test_agent_invocation_failure(self, mock_lambda, supervisor):
        """Test handling of agent invocation failure"""
        # Mock Lambda failure
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'error': 'Agent execution failed'
                })
            }).encode())
        }
        
        # Invoke agent
        payload = {'job_id': 'test-job-001'}
        result = supervisor._invoke_agent('sourcing', payload)
        
        # Verify error handling
        assert result['status'] == 'error'
        assert 'error' in result
    
    @patch('agents.supervisor_agent.lambda_client')
    @patch('agents.supervisor_agent.get_from_dynamodb')
    @patch('agents.supervisor_agent.save_to_dynamodb')
    def test_workflow_stops_on_agent_failure(
        self, mock_save, mock_get, mock_lambda, supervisor
    ):
        """Test that workflow stops when an agent fails"""
        workflow_state = {
            'workflow_id': 'workflow-123',
            'job_id': 'test-job-001',
            'status': 'in_progress',
            'completed_tasks': [],
            'tasks': [
                {'agent': 'sourcing', 'parameters': {}},
                {'agent': 'screening', 'parameters': {}}
            ]
        }
        
        # Mock first agent success, second agent failure
        call_count = [0]
        def mock_invoke_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call succeeds
                response = {
                    'status': 'success',
                    'data': {'candidates': []}
                }
            else:
                # Second call fails
                response = {
                    'status': 'error',
                    'error': 'Screening failed'
                }
            
            return {
                'StatusCode': 200,
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200 if call_count[0] == 1 else 500,
                    'body': json.dumps(response)
                }).encode())
            }
        
        mock_lambda.invoke.side_effect = mock_invoke_side_effect
        mock_save.return_value = {'success': True}
        
        # Execute workflow
        result = supervisor._execute_workflow(workflow_state)
        
        # Verify workflow failed
        assert result['status'] == 'failed'
        assert result['failed_at_task'] == 1
        assert len(result['completed_tasks']) == 1
    
    def test_workflow_summary_generation(self, supervisor):
        """Test workflow summary generation"""
        results = [
            {
                'status': 'success',
                'data': {
                    'summary': {
                        'candidates_found': 50,
                        'sources': ['linkedin', 'github']
                    }
                }
            },
            {
                'status': 'success',
                'data': {
                    'summary': {
                        'qualified_candidates': 15,
                        'rejection_rate': 0.7
                    }
                }
            }
        ]
        
        summary = supervisor._generate_workflow_summary(results)
        
        # Verify summary contains data from all agents
        assert summary['total_tasks'] == 2
        assert summary['successful_tasks'] == 2
        assert summary['candidates_found'] == 50
        assert summary['qualified_candidates'] == 15


class TestLambdaHandler:
    """Test Lambda handler function"""
    
    @patch('agents.supervisor_agent.SupervisorAgent')
    def test_lambda_handler_start_workflow(self, mock_supervisor_class):
        """Test Lambda handler for starting workflow"""
        # Mock supervisor instance
        mock_supervisor = Mock()
        mock_supervisor.start_workflow.return_value = {
            'status': 'success',
            'data': {'state_id': 'state-123'}
        }
        mock_supervisor_class.return_value = mock_supervisor
        
        # Create event
        event = {
            'action': 'start_workflow',
            'job_id': 'test-job-001'
        }
        
        # Invoke handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        mock_supervisor.start_workflow.assert_called_once_with('test-job-001', None)
    
    @patch('agents.supervisor_agent.SupervisorAgent')
    def test_lambda_handler_execute_next_step(self, mock_supervisor_class):
        """Test Lambda handler for executing next step"""
        mock_supervisor = Mock()
        mock_supervisor.execute_next_step.return_value = {
            'status': 'success',
            'data': {'next_agent': 'SourcingAgent'}
        }
        mock_supervisor_class.return_value = mock_supervisor
        
        event = {
            'action': 'execute_next_step',
            'state_id': 'state-123'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
