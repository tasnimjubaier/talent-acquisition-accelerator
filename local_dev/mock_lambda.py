"""
Mock Lambda Service for Local Development

Simulates AWS Lambda invocations for local agent testing.
Allows running agents locally without deploying to AWS.

Usage:
    from local_dev.mock_lambda import MockLambdaClient
    
    client = MockLambdaClient()
    response = client.invoke(
        FunctionName='supervisor-agent',
        InvocationType='RequestResponse',
        Payload=json.dumps({'operation': 'start_workflow', 'jobId': 'job-123'})
    )

References:
- 07_system_architecture.md: Multi-agent architecture
- 17_testing_strategy.md: Local testing approach
"""

import json
import sys
import os
from typing import Dict, Any, Optional
from io import BytesIO

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class MockLambdaContext:
    """Mock Lambda context object"""
    
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.function_version = '$LATEST'
        self.invoked_function_arn = f'arn:aws:lambda:us-east-1:123456789012:function:{function_name}'
        self.memory_limit_in_mb = '512'
        self.aws_request_id = f'mock-request-{function_name}'
        self.log_group_name = f'/aws/lambda/{function_name}'
        self.log_stream_name = '2024/03/15/[$LATEST]mock'
    
    def get_remaining_time_in_millis(self) -> int:
        """Get remaining execution time"""
        return 300000  # 5 minutes


class MockLambdaClient:
    """Mock Lambda client for local agent invocation"""
    
    def __init__(self, use_mock_services: bool = True):
        """
        Initialize mock Lambda client
        
        Args:
            use_mock_services: Whether to use mock Bedrock/DynamoDB
        """
        self.use_mock_services = use_mock_services
        self.invocation_count = 0
        
        # Patch AWS clients if using mock services
        if self.use_mock_services:
            self._patch_aws_clients()
    
    def invoke(
        self,
        FunctionName: str,
        InvocationType: str = 'RequestResponse',
        Payload: str = '{}',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke Lambda function locally
        
        Args:
            FunctionName: Name of the Lambda function
            InvocationType: Invocation type (RequestResponse, Event, DryRun)
            Payload: JSON payload string
            
        Returns:
            Response dict with StatusCode and Payload
        """
        self.invocation_count += 1
        
        # Parse payload
        event = json.loads(Payload) if isinstance(Payload, str) else Payload
        
        # Create mock context
        context = MockLambdaContext(FunctionName)
        
        # Route to appropriate handler
        try:
            result = self._invoke_handler(FunctionName, event, context)
            
            # Format response
            response_payload = json.dumps(result)
            
            return {
                'StatusCode': 200,
                'Payload': BytesIO(response_payload.encode('utf-8')),
                'ExecutedVersion': '$LATEST',
                'ResponseMetadata': {
                    'RequestId': f'mock-invoke-{self.invocation_count}',
                    'HTTPStatusCode': 200
                }
            }
            
        except Exception as e:
            error_payload = json.dumps({
                'errorMessage': str(e),
                'errorType': type(e).__name__
            })
            
            return {
                'StatusCode': 200,
                'FunctionError': 'Unhandled',
                'Payload': BytesIO(error_payload.encode('utf-8')),
                'ExecutedVersion': '$LATEST',
                'ResponseMetadata': {
                    'RequestId': f'mock-invoke-{self.invocation_count}',
                    'HTTPStatusCode': 200
                }
            }

    def _invoke_handler(self, function_name: str, event: Dict, context: MockLambdaContext) -> Dict[str, Any]:
        """Route invocation to appropriate agent handler"""
        
        # Import agent handlers
        from agents.supervisor_agent import lambda_handler as supervisor_handler
        from agents.sourcing_agent import lambda_handler as sourcing_handler
        from agents.screening_agent import lambda_handler as screening_handler
        from agents.outreach_agent import lambda_handler as outreach_handler
        from agents.scheduling_agent import lambda_handler as scheduling_handler
        from agents.evaluation_agent import lambda_handler as evaluation_handler
        
        # Map function names to handlers
        handlers = {
            'supervisor-agent': supervisor_handler,
            'sourcing-agent': sourcing_handler,
            'screening-agent': screening_handler,
            'outreach-agent': outreach_handler,
            'scheduling-agent': scheduling_handler,
            'evaluation-agent': evaluation_handler
        }
        
        handler = handlers.get(function_name)
        if not handler:
            raise ValueError(f"Unknown function: {function_name}")
        
        # Invoke handler
        return handler(event, context)
    
    def _patch_aws_clients(self):
        """Patch AWS clients to use mock services"""
        from local_dev.mock_bedrock import get_mock_bedrock_client
        from local_dev.mock_dynamodb import get_mock_dynamodb_resource
        
        # Patch in shared.utils
        import shared.utils as utils
        utils.bedrock_runtime = get_mock_bedrock_client()
        utils.dynamodb = get_mock_dynamodb_resource()


def get_mock_lambda_client(use_mock_services: bool = True) -> MockLambdaClient:
    """
    Get mock Lambda client instance
    
    Args:
        use_mock_services: Whether to use mock Bedrock/DynamoDB
        
    Returns:
        MockLambdaClient instance
    """
    return MockLambdaClient(use_mock_services=use_mock_services)
