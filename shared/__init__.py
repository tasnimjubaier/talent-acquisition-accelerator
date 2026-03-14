"""
Shared module for Talent Acquisition Accelerator

This module provides common utilities, configuration, and data models
used across all agents in the multi-agent recruiting system.
"""

from shared.config import Config
from shared.models import (
    Job,
    Candidate,
    Interaction,
    AgentState,
    JobStatus,
    CandidateStatus,
    InteractionType,
    from_dynamodb_item
)
from shared.utils import (
    invoke_bedrock,
    save_to_dynamodb,
    get_from_dynamodb,
    update_dynamodb_item,
    query_dynamodb,
    generate_id,
    get_timestamp,
    format_error_response,
    format_success_response,
    validate_required_fields,
    truncate_text,
    calculate_percentage,
    track_agent_cost,
    check_budget_alert,
    log_agent_execution,
    log_performance_metrics
)

__all__ = [
    # Config
    'Config',
    
    # Models
    'Job',
    'Candidate',
    'Interaction',
    'AgentState',
    'JobStatus',
    'CandidateStatus',
    'InteractionType',
    'from_dynamodb_item',
    
    # Bedrock utilities
    'invoke_bedrock',
    
    # DynamoDB utilities
    'save_to_dynamodb',
    'get_from_dynamodb',
    'update_dynamodb_item',
    'query_dynamodb',
    
    # Helper utilities
    'generate_id',
    'get_timestamp',
    'format_error_response',
    'format_success_response',
    'validate_required_fields',
    'truncate_text',
    'calculate_percentage',
    
    # Cost tracking
    'track_agent_cost',
    'check_budget_alert',
    
    # Logging
    'log_agent_execution',
    'log_performance_metrics'
]
