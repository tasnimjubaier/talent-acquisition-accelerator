"""
Supervisor Agent - Orchestrates Multi-Agent Recruiting Workflow

The Supervisor Agent coordinates all worker agents (Sourcing, Screening, Outreach,
Scheduling, Evaluation) to execute end-to-end recruiting workflows. It handles:
- Task decomposition (breaking down recruiting requests into agent tasks)
- Agent routing (determining which agent to invoke next)
- Result aggregation (combining outputs from all agents)
- Workflow state management (tracking progress through pipeline)
- Error handling and recovery

References:
- 07_system_architecture.md: Multi-agent orchestration pattern
- 08_agent_specifications.md: Supervisor agent requirements
- 09_agent_coordination_protocol.md: Inter-agent communication
- 16_module_build_checklist.md: Phase 3 implementation requirements

Verification Sources:
- Multi-Agent Orchestration Patterns: https://beyondscale.tech/blog/multi-agent-systems-architecture-patterns
- Supervisor Pattern: https://www.arunbaby.com/ai-agents/0029-multi-agent-architectures/
- CrewAI Framework: https://markaicode.com/crewai-framework-tutorial-multi-agent-llm-applications
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import boto3

from shared.utils import (
    invoke_bedrock,
    save_to_dynamodb,
    get_from_dynamodb,
    update_dynamodb_item,
    format_error_response,
    format_success_response,
    log_agent_execution,
    track_agent_cost,
    get_timestamp
)
from shared.config import Config
from shared.models import AgentState, Job, Candidate

logger = logging.getLogger()
logger.setLevel(Config.LOG_LEVEL)

# Initialize Lambda client for agent invocation
lambda_client = boto3.client('lambda', region_name=Config.AWS_REGION)


class SupervisorAgent:
    """
    Supervisor Agent for orchestrating multi-agent recruiting workflows
    
    The supervisor implements a hierarchical coordination pattern where it:
    1. Receives high-level recruiting requests (e.g., "Fill Software Engineer role")
    2. Decomposes requests into sequential tasks for worker agents
    3. Routes tasks to appropriate agents based on workflow stage
    4. Aggregates results and maintains shared context
    5. Handles errors and provides human checkpoints
    
    Workflow Sequence:
        Job Posted → Sourcing → Screening → Outreach → Scheduling → Evaluation → Hire
    """
    
    def __init__(self):
        """Initialize Supervisor Agent"""
        self.agent_name = "SupervisorAgent"
        self.agent_pipeline = [
            "SourcingAgent",
            "ScreeningAgent",
            "OutreachAgent",
            "SchedulingAgent",
            "EvaluationAgent"
        ]
        
        log_agent_execution(
            self.agent_name,
            "Initialized",
            {"pipeline": self.agent_pipeline}
        )
    
    def _invoke_agent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke worker agent Lambda function
        
        This method handles Lambda-to-Lambda invocation for worker agents.
        It sends the payload to the specified agent and returns the response.
        
        Args:
            agent_name: Name of agent (sourcing, screening, outreach, scheduling, evaluation)
            payload: Task payload for agent
            
        Returns:
            Agent response dict
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> result = supervisor._invoke_agent('sourcing', {'job_id': 'job-123'})
        
        Reference: 16_module_build_checklist.md - Phase 5, Step 5.1
        """
        function_name = f"talent-acq-{agent_name}"
        
        try:
            logger.info(f"Invoking {agent_name} agent (Lambda: {function_name})")
            
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            
            if response_payload.get('statusCode') == 200:
                body = json.loads(response_payload['body'])
                logger.info(f"{agent_name} agent completed successfully")
                return body
            else:
                error_msg = f"{agent_name} agent failed with status {response_payload.get('statusCode')}"
                logger.error(error_msg)
                return format_error_response(
                    error_msg,
                    {"response": response_payload},
                    "AgentInvocationFailed"
                )
                
        except Exception as e:
            logger.error(f"Failed to invoke {agent_name}: {str(e)}")
            return format_error_response(
                f"Lambda invocation failed: {str(e)}",
                {"agent_name": agent_name, "function_name": function_name},
                "LambdaInvocationError"
            )
    
    def _execute_workflow(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow tasks sequentially with agent invocation
        
        This method orchestrates the complete workflow by:
        1. Iterating through all tasks in sequence
        2. Invoking the appropriate agent for each task
        3. Passing results from previous tasks to next tasks
        4. Stopping workflow if any agent fails
        5. Saving state after each task completion
        
        Args:
            workflow_state: Dict containing workflow configuration and state
                - workflow_id: Unique workflow identifier
                - job_id: Job ID being recruited for
                - tasks: List of tasks to execute
                - completed_tasks: List of completed tasks (updated during execution)
                
        Returns:
            Dict with workflow execution results
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> workflow_state = {
            >>>     'workflow_id': 'wf-123',
            >>>     'job_id': 'job-456',
            >>>     'tasks': [
            >>>         {'agent': 'sourcing', 'parameters': {'target_count': 50}},
            >>>         {'agent': 'screening', 'parameters': {'min_score': 0.7}}
            >>>     ],
            >>>     'completed_tasks': []
            >>> }
            >>> result = supervisor._execute_workflow(workflow_state)
        
        Reference: 16_module_build_checklist.md - Phase 5, Step 5.1
        """
        tasks = workflow_state['tasks']
        results = []
        
        logger.info(f"Executing workflow {workflow_state['workflow_id']} with {len(tasks)} tasks")
        
        for i, task in enumerate(tasks):
            agent_name = task['agent']
            
            # Check if task depends on previous task
            if task.get('depends_on'):
                # Get results from previous task
                prev_results = results[-1] if results else {}
                task['parameters']['previous_results'] = prev_results
            
            # Invoke agent
            logger.info(f"Executing task {i+1}/{len(tasks)}: {agent_name}")
            result = self._invoke_agent(agent_name, task)
            
            if result.get('status') != 'success':
                # Task failed - stop workflow
                logger.error(f"Workflow failed at task {i}: {agent_name}")
                return {
                    'workflow_id': workflow_state['workflow_id'],
                    'status': 'failed',
                    'failed_at_task': i,
                    'error': result.get('error', 'Unknown error'),
                    'completed_tasks': results
                }
            
            results.append(result)
            
            # Update workflow state
            workflow_state['completed_tasks'].append({
                'task_index': i,
                'agent': agent_name,
                'result': result,
                'completed_at': get_timestamp()
            })
            
            # Save state to DynamoDB
            save_to_dynamodb(Config.AGENT_STATE_TABLE, {
                'stateId': workflow_state['workflow_id'],
                'agentType': 'supervisor',
                'state': workflow_state,
                'lastUpdated': get_timestamp()
            })
        
        # All tasks completed successfully
        workflow_state['status'] = 'completed'
        
        logger.info(f"Workflow {workflow_state['workflow_id']} completed successfully")
        
        return {
            'workflow_id': workflow_state['workflow_id'],
            'status': 'completed',
            'results': results,
            'summary': self._generate_workflow_summary(results)
        }
    
    def _generate_workflow_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate human-readable workflow summary from agent results
        
        Aggregates key metrics from all agent executions into a concise summary.
        
        Args:
            results: List of result dicts from each agent
            
        Returns:
            Dict with aggregated summary metrics
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> results = [
            >>>     {'status': 'success', 'data': {'summary': {'candidates_found': 50}}},
            >>>     {'status': 'success', 'data': {'summary': {'qualified': 15}}}
            >>> ]
            >>> summary = supervisor._generate_workflow_summary(results)
            >>> print(summary['total_tasks'])  # 2
        
        Reference: 16_module_build_checklist.md - Phase 5, Step 5.1
        """
        summary = {
            'total_tasks': len(results),
            'successful_tasks': sum(1 for r in results if r.get('status') == 'success')
        }
        
        # Extract key metrics from each agent
        for result in results:
            if 'data' in result:
                data = result['data']
                if 'summary' in data:
                    # Merge agent-specific summaries
                    summary.update(data['summary'])
        
        logger.info(f"Generated workflow summary: {summary}")
        
        return summary
    
    def start_workflow(self, job_id: str, workflow_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a new recruiting workflow for a job
        
        Args:
            job_id: Job ID to recruit for
            workflow_config: Optional configuration (e.g., candidate count, sourcing strategy)
            
        Returns:
            Dict with workflow state and initial status
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> result = supervisor.start_workflow("job-123", {"target_candidates": 50})
        """
        log_agent_execution(
            self.agent_name,
            "Starting workflow",
            {"job_id": job_id, "config": workflow_config}
        )
        
        try:
            # Verify job exists
            job_item = get_from_dynamodb(Config.JOBS_TABLE, {'jobId': job_id})
            if not job_item:
                return format_error_response(
                    f"Job {job_id} not found",
                    {"job_id": job_id},
                    "JobNotFound"
                )
            
            # Create initial agent state
            agent_state = AgentState(
                job_id=job_id,
                current_agent=None,
                workflow_status="initialized",
                agents_executed=[],
                current_step=0,
                total_steps=len(self.agent_pipeline),
                shared_context={
                    "job_id": job_id,
                    "workflow_config": workflow_config or {},
                    "started_at": get_timestamp()
                },
                agent_results={}
            )
            
            # Save agent state to DynamoDB
            save_result = save_to_dynamodb(
                Config.AGENT_STATE_TABLE,
                agent_state.to_dynamodb_item()
            )
            
            if not save_result['success']:
                return format_error_response(
                    "Failed to initialize workflow state",
                    {"error": save_result.get('error')},
                    "StateInitializationFailed"
                )
            
            log_agent_execution(
                self.agent_name,
                "Workflow initialized",
                {
                    "state_id": agent_state.state_id,
                    "job_id": job_id,
                    "total_steps": agent_state.total_steps
                }
            )
            
            return format_success_response(
                {
                    "state_id": agent_state.state_id,
                    "job_id": job_id,
                    "workflow_status": "initialized",
                    "next_agent": self.agent_pipeline[0],
                    "message": "Workflow initialized successfully"
                },
                {
                    "total_steps": agent_state.total_steps,
                    "pipeline": self.agent_pipeline
                }
            )
            
        except Exception as e:
            logger.error(f"Error starting workflow: {str(e)}")
            return format_error_response(
                f"Failed to start workflow: {str(e)}",
                {"job_id": job_id},
                "WorkflowStartFailed"
            )

    
    def execute_next_step(self, state_id: str) -> Dict[str, Any]:
        """
        Execute the next step in the workflow pipeline
        
        This method:
        1. Retrieves current workflow state
        2. Determines next agent to execute
        3. Prepares context for the agent
        4. Returns instructions for agent execution
        
        Args:
            state_id: Agent state ID
            
        Returns:
            Dict with next agent to execute and context
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> result = supervisor.execute_next_step("state-123")
            >>> print(result['data']['next_agent'])  # "SourcingAgent"
        """
        log_agent_execution(
            self.agent_name,
            "Executing next step",
            {"state_id": state_id}
        )
        
        try:
            # Retrieve current state
            state_item = get_from_dynamodb(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id}
            )
            
            if not state_item:
                return format_error_response(
                    f"Workflow state {state_id} not found",
                    {"state_id": state_id},
                    "StateNotFound"
                )
            
            # Check if workflow is already completed
            if state_item['workflowStatus'] == 'completed':
                return format_success_response(
                    {
                        "message": "Workflow already completed",
                        "state_id": state_id,
                        "workflow_status": "completed"
                    }
                )
            
            # Determine next agent
            current_step = state_item['currentStep']
            
            if current_step >= len(self.agent_pipeline):
                # All agents executed, mark as completed
                update_dynamodb_item(
                    Config.AGENT_STATE_TABLE,
                    {'stateId': state_id},
                    {
                        'workflowStatus': 'completed',
                        'completedAt': get_timestamp()
                    }
                )
                
                return format_success_response(
                    {
                        "message": "All agents executed successfully",
                        "state_id": state_id,
                        "workflow_status": "completed",
                        "agents_executed": state_item['agentsExecuted']
                    }
                )
            
            next_agent = self.agent_pipeline[current_step]
            
            # Update state to in_progress
            update_dynamodb_item(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id},
                {
                    'currentAgent': next_agent,
                    'workflowStatus': 'in_progress'
                }
            )
            
            log_agent_execution(
                self.agent_name,
                "Next step determined",
                {
                    "state_id": state_id,
                    "next_agent": next_agent,
                    "step": f"{current_step + 1}/{len(self.agent_pipeline)}"
                }
            )
            
            return format_success_response(
                {
                    "next_agent": next_agent,
                    "state_id": state_id,
                    "current_step": current_step + 1,
                    "total_steps": len(self.agent_pipeline),
                    "shared_context": state_item.get('sharedContext', {}),
                    "previous_results": state_item.get('agentResults', {})
                },
                {
                    "job_id": state_item['jobId'],
                    "agents_executed": state_item['agentsExecuted']
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing next step: {str(e)}")
            return format_error_response(
                f"Failed to execute next step: {str(e)}",
                {"state_id": state_id},
                "NextStepFailed"
            )
    
    def record_agent_result(
        self,
        state_id: str,
        agent_name: str,
        result: Dict[str, Any],
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> Dict[str, Any]:
        """
        Record the result from an agent execution
        
        Args:
            state_id: Agent state ID
            agent_name: Name of the agent that executed
            result: Result data from the agent
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            
        Returns:
            Dict with success status
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> supervisor.record_agent_result(
            >>>     "state-123",
            >>>     "SourcingAgent",
            >>>     {"candidates_found": 50},
            >>>     input_tokens=1000,
            >>>     output_tokens=500
            >>> )
        """
        log_agent_execution(
            self.agent_name,
            "Recording agent result",
            {"state_id": state_id, "agent_name": agent_name}
        )
        
        try:
            # Retrieve current state
            state_item = get_from_dynamodb(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id}
            )
            
            if not state_item:
                return format_error_response(
                    f"Workflow state {state_id} not found",
                    {"state_id": state_id},
                    "StateNotFound"
                )
            
            # Update agent results
            agent_results = state_item.get('agentResults', {})
            agent_results[agent_name] = {
                'result': result,
                'timestamp': get_timestamp(),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
            
            # Update agents executed list
            agents_executed = state_item.get('agentsExecuted', [])
            if agent_name not in agents_executed:
                agents_executed.append(agent_name)
            
            # Calculate cumulative cost
            total_input_tokens = state_item.get('totalInputTokens', 0) + input_tokens
            total_output_tokens = state_item.get('totalOutputTokens', 0) + output_tokens
            total_cost = Config.calculate_cost(total_input_tokens, total_output_tokens)
            
            # Update state
            update_result = update_dynamodb_item(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id},
                {
                    'agentResults': agent_results,
                    'agentsExecuted': agents_executed,
                    'currentStep': len(agents_executed),
                    'totalInputTokens': total_input_tokens,
                    'totalOutputTokens': total_output_tokens,
                    'totalCostUsd': total_cost
                }
            )
            
            if not update_result['success']:
                return format_error_response(
                    "Failed to record agent result",
                    {"error": update_result.get('error')},
                    "RecordResultFailed"
                )
            
            log_agent_execution(
                self.agent_name,
                "Agent result recorded",
                {
                    "state_id": state_id,
                    "agent_name": agent_name,
                    "total_cost": f"${total_cost:.4f}",
                    "agents_completed": len(agents_executed)
                }
            )
            
            return format_success_response(
                {
                    "message": "Agent result recorded successfully",
                    "state_id": state_id,
                    "agent_name": agent_name,
                    "agents_completed": len(agents_executed),
                    "total_steps": len(self.agent_pipeline),
                    "total_cost_usd": total_cost
                }
            )
            
        except Exception as e:
            logger.error(f"Error recording agent result: {str(e)}")
            return format_error_response(
                f"Failed to record agent result: {str(e)}",
                {"state_id": state_id, "agent_name": agent_name},
                "RecordResultFailed"
            )

    
    def decompose_task(self, job_id: str, request: str) -> Dict[str, Any]:
        """
        Decompose a high-level recruiting request into agent tasks
        
        Uses Amazon Nova to analyze the request and determine:
        - Which agents need to be involved
        - What parameters each agent needs
        - What the expected outcomes are
        
        Args:
            job_id: Job ID
            request: High-level recruiting request (e.g., "Find 50 qualified candidates")
            
        Returns:
            Dict with decomposed tasks for each agent
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> result = supervisor.decompose_task(
            >>>     "job-123",
            >>>     "Find and screen 50 software engineers with Python experience"
            >>> )
        """
        log_agent_execution(
            self.agent_name,
            "Decomposing task",
            {"job_id": job_id, "request": request}
        )
        
        try:
            # Get job details
            job_item = get_from_dynamodb(Config.JOBS_TABLE, {'jobId': job_id})
            if not job_item:
                return format_error_response(
                    f"Job {job_id} not found",
                    {"job_id": job_id},
                    "JobNotFound"
                )
            
            # Build prompt for Nova to decompose the task
            system_prompt = """You are a recruiting workflow expert. Your job is to decompose high-level recruiting requests into specific tasks for specialized agents.

The available agents are:
1. SourcingAgent - Finds candidates from various sources (LinkedIn, GitHub, job boards)
2. ScreeningAgent - Evaluates candidates against job requirements
3. OutreachAgent - Engages candidates with personalized messages
4. SchedulingAgent - Coordinates interview scheduling
5. EvaluationAgent - Synthesizes feedback and provides hiring recommendations

Analyze the request and provide a JSON response with tasks for each agent."""

            prompt = f"""Job Details:
Title: {job_item.get('title', 'N/A')}
Description: {job_item.get('description', 'N/A')}
Requirements: {json.dumps(job_item.get('requirements', {}), indent=2)}

Recruiting Request: {request}

Decompose this request into specific tasks for each agent. Return a JSON object with this structure:
{{
  "sourcing": {{
    "target_count": <number of candidates to source>,
    "sources": ["linkedin", "github", "job_boards"],
    "criteria": "specific sourcing criteria"
  }},
  "screening": {{
    "evaluation_criteria": ["skill1", "skill2"],
    "pass_threshold": 0.7
  }},
  "outreach": {{
    "message_tone": "professional/casual",
    "channels": ["email", "linkedin"]
  }},
  "scheduling": {{
    "interview_type": "technical/behavioral",
    "duration_minutes": 60
  }},
  "evaluation": {{
    "focus_areas": ["technical_skills", "culture_fit"]
  }}
}}"""

            # Invoke Nova for task decomposition
            nova_result = invoke_bedrock(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            if not nova_result['success']:
                return format_error_response(
                    "Failed to decompose task using Nova",
                    {"error": nova_result.get('error')},
                    "TaskDecompositionFailed"
                )
            
            # Parse Nova's response
            try:
                task_breakdown = json.loads(nova_result['content'])
            except json.JSONDecodeError:
                # If Nova didn't return valid JSON, use defaults
                logger.warning("Nova response was not valid JSON, using default task breakdown")
                task_breakdown = {
                    "sourcing": {"target_count": 50, "sources": ["linkedin", "github"]},
                    "screening": {"evaluation_criteria": ["skills", "experience"], "pass_threshold": 0.7},
                    "outreach": {"message_tone": "professional", "channels": ["email"]},
                    "scheduling": {"interview_type": "technical", "duration_minutes": 60},
                    "evaluation": {"focus_areas": ["technical_skills", "experience"]}
                }
            
            log_agent_execution(
                self.agent_name,
                "Task decomposed",
                {
                    "job_id": job_id,
                    "agents_involved": len(task_breakdown),
                    "cost": f"${nova_result.get('cost_usd', 0):.4f}"
                }
            )
            
            return format_success_response(
                {
                    "job_id": job_id,
                    "task_breakdown": task_breakdown,
                    "agents_required": list(task_breakdown.keys())
                },
                {
                    "input_tokens": nova_result.get('input_tokens', 0),
                    "output_tokens": nova_result.get('output_tokens', 0),
                    "cost_usd": nova_result.get('cost_usd', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error decomposing task: {str(e)}")
            return format_error_response(
                f"Failed to decompose task: {str(e)}",
                {"job_id": job_id},
                "TaskDecompositionFailed"
            )
    
    def aggregate_results(self, state_id: str) -> Dict[str, Any]:
        """
        Aggregate results from all agents into a comprehensive report
        
        Args:
            state_id: Agent state ID
            
        Returns:
            Dict with aggregated results and summary
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> result = supervisor.aggregate_results("state-123")
            >>> print(result['data']['summary'])
        """
        log_agent_execution(
            self.agent_name,
            "Aggregating results",
            {"state_id": state_id}
        )
        
        try:
            # Retrieve workflow state
            state_item = get_from_dynamodb(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id}
            )
            
            if not state_item:
                return format_error_response(
                    f"Workflow state {state_id} not found",
                    {"state_id": state_id},
                    "StateNotFound"
                )
            
            agent_results = state_item.get('agentResults', {})
            
            # Build aggregation prompt for Nova
            system_prompt = """You are a recruiting analytics expert. Synthesize results from multiple recruiting agents into a comprehensive executive summary."""
            
            prompt = f"""Analyze the following results from our multi-agent recruiting system and provide a comprehensive summary:

Agent Results:
{json.dumps(agent_results, indent=2)}

Provide a JSON response with:
{{
  "executive_summary": "2-3 sentence overview of the recruiting process",
  "key_metrics": {{
    "candidates_sourced": <number>,
    "candidates_screened": <number>,
    "candidates_contacted": <number>,
    "interviews_scheduled": <number>,
    "top_candidates": <number>
  }},
  "highlights": ["highlight 1", "highlight 2", "highlight 3"],
  "concerns": ["concern 1", "concern 2"],
  "recommendations": ["recommendation 1", "recommendation 2"]
}}"""

            # Invoke Nova for aggregation
            nova_result = invoke_bedrock(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1500
            )
            
            if not nova_result['success']:
                # Return raw results if Nova fails
                return format_success_response(
                    {
                        "state_id": state_id,
                        "agent_results": agent_results,
                        "summary": "Aggregation completed (Nova unavailable)",
                        "total_cost_usd": state_item.get('totalCostUsd', 0)
                    }
                )
            
            # Parse Nova's aggregation
            try:
                aggregated_summary = json.loads(nova_result['content'])
            except json.JSONDecodeError:
                aggregated_summary = {
                    "executive_summary": "Workflow completed successfully",
                    "key_metrics": {},
                    "highlights": [],
                    "concerns": [],
                    "recommendations": []
                }
            
            log_agent_execution(
                self.agent_name,
                "Results aggregated",
                {
                    "state_id": state_id,
                    "agents_processed": len(agent_results),
                    "total_cost": f"${state_item.get('totalCostUsd', 0):.4f}"
                }
            )
            
            return format_success_response(
                {
                    "state_id": state_id,
                    "job_id": state_item['jobId'],
                    "workflow_status": state_item['workflowStatus'],
                    "summary": aggregated_summary,
                    "agent_results": agent_results,
                    "total_cost_usd": state_item.get('totalCostUsd', 0),
                    "total_input_tokens": state_item.get('totalInputTokens', 0),
                    "total_output_tokens": state_item.get('totalOutputTokens', 0)
                },
                {
                    "agents_executed": state_item.get('agentsExecuted', []),
                    "completed_at": state_item.get('completedAt')
                }
            )
            
        except Exception as e:
            logger.error(f"Error aggregating results: {str(e)}")
            return format_error_response(
                f"Failed to aggregate results: {str(e)}",
                {"state_id": state_id},
                "AggregationFailed"
            )

    
    def handle_error(
        self,
        state_id: str,
        agent_name: str,
        error: str,
        error_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle errors during agent execution
        
        Args:
            state_id: Agent state ID
            agent_name: Name of agent that encountered error
            error: Error message
            error_context: Optional error context
            
        Returns:
            Dict with error handling result
        """
        log_agent_execution(
            self.agent_name,
            "Handling error",
            {"state_id": state_id, "agent_name": agent_name, "error": error},
            level="ERROR"
        )
        
        try:
            # Retrieve current state
            state_item = get_from_dynamodb(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id}
            )
            
            if not state_item:
                return format_error_response(
                    f"Workflow state {state_id} not found",
                    {"state_id": state_id},
                    "StateNotFound"
                )
            
            # Record error
            errors = state_item.get('errors', [])
            errors.append({
                'agent_name': agent_name,
                'error': error,
                'context': error_context or {},
                'timestamp': get_timestamp()
            })
            
            # Update state
            update_dynamodb_item(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id},
                {
                    'errors': errors,
                    'workflowStatus': 'failed'
                }
            )
            
            return format_error_response(
                f"Agent {agent_name} failed: {error}",
                {
                    "state_id": state_id,
                    "agent_name": agent_name,
                    "error_count": len(errors)
                },
                "AgentExecutionFailed"
            )
            
        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")
            return format_error_response(
                f"Failed to handle error: {str(e)}",
                {"state_id": state_id},
                "ErrorHandlingFailed"
            )

    
    def get_workflow_status(self, state_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow
        
        Args:
            state_id: Agent state ID
            
        Returns:
            Dict with workflow status and progress
        """
        try:
            state_item = get_from_dynamodb(
                Config.AGENT_STATE_TABLE,
                {'stateId': state_id}
            )
            
            if not state_item:
                return format_error_response(
                    f"Workflow state {state_id} not found",
                    {"state_id": state_id},
                    "StateNotFound"
                )
            
            progress_percentage = (
                state_item.get('currentStep', 0) / state_item.get('totalSteps', 1)
            ) * 100
            
            return format_success_response(
                {
                    "state_id": state_id,
                    "job_id": state_item['jobId'],
                    "workflow_status": state_item['workflowStatus'],
                    "current_agent": state_item.get('currentAgent'),
                    "current_step": state_item.get('currentStep', 0),
                    "total_steps": state_item.get('totalSteps', 0),
                    "progress_percentage": round(progress_percentage, 1),
                    "agents_executed": state_item.get('agentsExecuted', []),
                    "total_cost_usd": state_item.get('totalCostUsd', 0),
                    "errors": state_item.get('errors', [])
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return format_error_response(
                f"Failed to get workflow status: {str(e)}",
                {"state_id": state_id},
                "StatusRetrievalFailed"
            )


# ============================================================================
# Lambda Handler (for AWS Lambda deployment)
# ============================================================================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Supervisor Agent
    
    Supported operations:
    - start_workflow: Initialize new recruiting workflow
    - execute_next_step: Execute next agent in pipeline
    - record_result: Record agent execution result
    - decompose_task: Decompose recruiting request into tasks
    - aggregate_results: Aggregate results from all agents
    - get_status: Get workflow status
    - handle_error: Handle agent execution error
    
    Args:
        event: Lambda event with operation and parameters
        context: Lambda context
        
    Returns:
        Response dict
    """
    supervisor = SupervisorAgent()
    
    operation = event.get('operation')
    
    if operation == 'start_workflow':
        return supervisor.start_workflow(
            job_id=event['job_id'],
            workflow_config=event.get('workflow_config')
        )
    
    elif operation == 'execute_next_step':
        return supervisor.execute_next_step(state_id=event['state_id'])
    
    elif operation == 'record_result':
        return supervisor.record_agent_result(
            state_id=event['state_id'],
            agent_name=event['agent_name'],
            result=event['result'],
            input_tokens=event.get('input_tokens', 0),
            output_tokens=event.get('output_tokens', 0)
        )
    
    elif operation == 'decompose_task':
        return supervisor.decompose_task(
            job_id=event['job_id'],
            request=event['request']
        )
    
    elif operation == 'aggregate_results':
        return supervisor.aggregate_results(state_id=event['state_id'])
    
    elif operation == 'get_status':
        return supervisor.get_workflow_status(state_id=event['state_id'])
    
    elif operation == 'handle_error':
        return supervisor.handle_error(
            state_id=event['state_id'],
            agent_name=event['agent_name'],
            error=event['error'],
            error_context=event.get('error_context')
        )
    
    else:
        return format_error_response(
            f"Unknown operation: {operation}",
            {"operation": operation},
            "UnknownOperation"
        )
