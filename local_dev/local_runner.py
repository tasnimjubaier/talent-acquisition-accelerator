"""
Local Workflow Runner

Runs complete talent acquisition workflow locally without AWS costs.
Provides detailed logging, step-by-step execution, and cost simulation.

Usage:
    python local_dev/local_runner.py --job-file demo/01_sample_jobs.json --job-index 0
    
    # Or programmatically:
    from local_dev.local_runner import LocalRunner
    
    runner = LocalRunner()
    result = runner.run_workflow(job_data)

References:
- 15_development_roadmap.md: Workflow sequence
- 17_testing_strategy.md: Local testing approach
"""

import json
import sys
import os
import argparse
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import mock services
from local_dev.mock_bedrock import get_mock_bedrock_client
from local_dev.mock_dynamodb import get_mock_dynamodb_resource
from local_dev.mock_lambda import get_mock_lambda_client

# Import shared utilities
from shared.config import Config
from shared.models import Job, AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalRunner:
    """Local workflow runner for testing without AWS"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize local runner
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.bedrock_client = get_mock_bedrock_client()
        self.dynamodb = get_mock_dynamodb_resource()
        self.lambda_client = get_mock_lambda_client(use_mock_services=True)
        
        # Patch AWS clients in shared.utils
        import shared.utils as utils
        utils.bedrock_runtime = self.bedrock_client
        utils.dynamodb = self.dynamodb
        
        # Workflow tracking
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.execution_times = {}
        
        if self.verbose:
            logger.info("Local runner initialized with mock services")
    
    def run_workflow(self, job_data: Dict[str, Any], step_by_step: bool = False) -> Dict[str, Any]:
        """
        Run complete workflow locally
        
        Args:
            job_data: Job posting data
            step_by_step: Pause after each agent for review
            
        Returns:
            Workflow results
        """
        logger.info("=" * 80)
        logger.info("STARTING LOCAL WORKFLOW EXECUTION")
        logger.info("=" * 80)
        
        # Create job
        job = Job(**job_data)
        logger.info(f"Job created: {job.job_id} - {job.title}")
        
        # Save job to mock DynamoDB
        jobs_table = self.dynamodb.Table(Config.JOBS_TABLE)
        jobs_table.put_item(Item=job.to_dynamodb_item())
        
        # Start workflow via supervisor
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Starting Workflow (Supervisor Agent)")
        logger.info("=" * 80)
        
        start_payload = {
            'operation': 'start_workflow',
            'jobId': job.job_id
        }
        
        supervisor_response = self._invoke_agent('supervisor-agent', start_payload)
        
        if supervisor_response.get('status') != 'success':
            logger.error(f"Workflow failed to start: {supervisor_response.get('error')}")
            return supervisor_response
        
        state_id = supervisor_response['data']['stateId']
        logger.info(f"Workflow started with state ID: {state_id}")
        
        if step_by_step:
            input("\nPress Enter to continue to next step...")
        
        # Execute workflow steps
        agents = [
            ('sourcing-agent', 'STEP 2: Candidate Sourcing'),
            ('screening-agent', 'STEP 3: Candidate Screening'),
            ('outreach-agent', 'STEP 4: Personalized Outreach'),
            ('scheduling-agent', 'STEP 5: Interview Scheduling'),
            ('evaluation-agent', 'STEP 6: Final Evaluation')
        ]
        
        for agent_name, step_label in agents:
            logger.info("\n" + "=" * 80)
            logger.info(step_label)
            logger.info("=" * 80)
            
            execute_payload = {
                'operation': 'execute_agent',
                'stateId': state_id,
                'agentName': agent_name
            }
            
            agent_response = self._invoke_agent('supervisor-agent', execute_payload)
            
            if agent_response.get('status') != 'success':
                logger.error(f"Agent {agent_name} failed: {agent_response.get('error')}")
                return agent_response
            
            logger.info(f"✓ {agent_name} completed successfully")
            
            if step_by_step:
                input("\nPress Enter to continue to next step...")
        
        # Get final results
        logger.info("\n" + "=" * 80)
        logger.info("WORKFLOW COMPLETED - Retrieving Results")
        logger.info("=" * 80)
        
        results = self._get_workflow_results(state_id)
        
        # Display summary
        self._display_summary(results)
        
        return results
    
    def _invoke_agent(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke agent and track metrics"""
        start_time = datetime.now()
        
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.execution_times[function_name] = execution_time
        
        # Parse response
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes.decode('utf-8'))
        
        logger.info(f"Execution time: {execution_time:.2f}s")
        
        return result

    def _get_workflow_results(self, state_id: str) -> Dict[str, Any]:
        """Get workflow results from DynamoDB"""
        state_table = self.dynamodb.Table(Config.AGENT_STATE_TABLE)
        response = state_table.get_item(Key={'stateId': state_id})
        
        state_data = response.get('Item', {})
        
        # Get candidates
        candidates_table = self.dynamodb.Table(Config.CANDIDATES_TABLE)
        candidates_response = candidates_table.scan()
        candidates = candidates_response.get('Items', [])
        
        return {
            'state': state_data,
            'candidates': candidates,
            'metrics': {
                'total_cost_usd': state_data.get('totalCostUsd', 0.0),
                'total_input_tokens': state_data.get('totalInputTokens', 0),
                'total_output_tokens': state_data.get('totalOutputTokens', 0),
                'execution_times': self.execution_times
            }
        }
    
    def _display_summary(self, results: Dict[str, Any]):
        """Display workflow summary"""
        logger.info("\n" + "=" * 80)
        logger.info("WORKFLOW SUMMARY")
        logger.info("=" * 80)
        
        state = results.get('state', {})
        candidates = results.get('candidates', [])
        metrics = results.get('metrics', {})
        
        logger.info(f"\nWorkflow Status: {state.get('workflowStatus', 'unknown')}")
        logger.info(f"Agents Executed: {len(state.get('agentsExecuted', []))}/5")
        logger.info(f"Total Candidates: {len(candidates)}")
        
        # Cost summary
        logger.info("\n--- Cost Summary ---")
        logger.info(f"Total Cost: ${metrics.get('total_cost_usd', 0.0):.4f}")
        logger.info(f"Input Tokens: {metrics.get('total_input_tokens', 0):,}")
        logger.info(f"Output Tokens: {metrics.get('total_output_tokens', 0):,}")
        
        # Execution times
        logger.info("\n--- Execution Times ---")
        for agent, exec_time in metrics.get('execution_times', {}).items():
            logger.info(f"{agent}: {exec_time:.2f}s")
        
        # Top candidates
        if candidates:
            logger.info("\n--- Top 5 Candidates ---")
            sorted_candidates = sorted(
                candidates,
                key=lambda c: c.get('overallScore', 0.0),
                reverse=True
            )[:5]
            
            for i, candidate in enumerate(sorted_candidates, 1):
                logger.info(
                    f"{i}. {candidate.get('name', 'Unknown')} - "
                    f"Score: {candidate.get('overallScore', 0.0):.2f} - "
                    f"Status: {candidate.get('status', 'unknown')}"
                )
        
        logger.info("\n" + "=" * 80)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Run talent acquisition workflow locally')
    parser.add_argument('--job-file', required=True, help='Path to job JSON file')
    parser.add_argument('--job-index', type=int, default=0, help='Job index in file')
    parser.add_argument('--step-by-step', action='store_true', help='Pause after each step')
    parser.add_argument('--quiet', action='store_true', help='Reduce logging output')
    
    args = parser.parse_args()
    
    # Load job data
    with open(args.job_file, 'r') as f:
        jobs_data = json.load(f)
    
    if isinstance(jobs_data, list):
        job_data = jobs_data[args.job_index]
    else:
        job_data = jobs_data
    
    # Run workflow
    runner = LocalRunner(verbose=not args.quiet)
    results = runner.run_workflow(job_data, step_by_step=args.step_by_step)
    
    # Save results
    output_file = f"local_dev/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
