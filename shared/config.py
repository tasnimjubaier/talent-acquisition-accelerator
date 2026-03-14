"""
Configuration Management for Talent Acquisition Accelerator

This module centralizes all configuration values, environment variables,
and AWS service settings used across the multi-agent recruiting system.

References:
- 02_tech_stack_decisions.md: Technology choices and rationale
- 16_module_build_checklist.md: Phase 2 implementation requirements

Verification Sources:
- AWS Lambda Environment Variables: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
- Amazon Bedrock Configuration: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html
"""

import os
from typing import Optional


class Config:
    """Central configuration class for all system settings"""
    
    # ============================================================================
    # AWS Region Configuration
    # ============================================================================
    AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCOUNT_ID: Optional[str] = os.getenv('AWS_ACCOUNT_ID')
    
    # ============================================================================
    # DynamoDB Table Names
    # Reference: 16_module_build_checklist.md - Phase 1 infrastructure setup
    # ============================================================================
    CANDIDATES_TABLE: str = os.getenv('CANDIDATES_TABLE', 'talent-acq-candidates')
    JOBS_TABLE: str = os.getenv('JOBS_TABLE', 'talent-acq-jobs')
    INTERACTIONS_TABLE: str = os.getenv('INTERACTIONS_TABLE', 'talent-acq-interactions')
    AGENT_STATE_TABLE: str = os.getenv('AGENT_STATE_TABLE', 'talent-acq-agent-state')
    
    # ============================================================================
    # Amazon Bedrock / Nova Configuration
    # Reference: 02_tech_stack_decisions.md - Nova 2 Lite selected for cost efficiency
    # Pricing: $0.00006 per 1K input tokens, $0.00024 per 1K output tokens
    # ============================================================================
    BEDROCK_MODEL_ID: str = os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-lite-v1:0')
    
    # Model parameters optimized for recruiting tasks
    # Temperature: Lower for consistent, factual responses
    # Max tokens: Balanced for detailed responses without excessive cost
    MAX_TOKENS: int = int(os.getenv('MAX_TOKENS', '4096'))
    TEMPERATURE: float = float(os.getenv('TEMPERATURE', '0.3'))
    TOP_P: float = float(os.getenv('TOP_P', '0.9'))
    
    # ============================================================================
    # Agent Configuration
    # ============================================================================
    AGENT_TIMEOUT: int = int(os.getenv('AGENT_TIMEOUT', '300'))  # 5 minutes
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_BACKOFF_BASE: int = int(os.getenv('RETRY_BACKOFF_BASE', '2'))  # Exponential backoff
    
    # ============================================================================
    # Logging Configuration
    # ============================================================================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # ============================================================================
    # Cost Tracking Configuration
    # Reference: 02_tech_stack_decisions.md - Budget: $270 for demo period
    # ============================================================================
    # Nova 2 Lite pricing (per 1,000 tokens)
    COST_PER_1K_INPUT_TOKENS: float = 0.00006
    COST_PER_1K_OUTPUT_TOKENS: float = 0.00024
    
    # Budget alerts
    MONTHLY_BUDGET_USD: float = float(os.getenv('MONTHLY_BUDGET_USD', '270.0'))
    BUDGET_ALERT_THRESHOLD: float = float(os.getenv('BUDGET_ALERT_THRESHOLD', '0.8'))  # 80%
    
    # ============================================================================
    # Agent-Specific Configuration
    # ============================================================================
    
    # Sourcing Agent
    SOURCING_MAX_CANDIDATES: int = int(os.getenv('SOURCING_MAX_CANDIDATES', '100'))
    SOURCING_MIN_FIT_SCORE: float = float(os.getenv('SOURCING_MIN_FIT_SCORE', '0.7'))
    
    # Screening Agent
    SCREENING_PASS_THRESHOLD: float = float(os.getenv('SCREENING_PASS_THRESHOLD', '0.75'))
    
    # Outreach Agent
    OUTREACH_MAX_RETRIES: int = int(os.getenv('OUTREACH_MAX_RETRIES', '3'))
    
    # Scheduling Agent
    SCHEDULING_BUFFER_MINUTES: int = int(os.getenv('SCHEDULING_BUFFER_MINUTES', '15'))
    
    # Evaluation Agent
    EVALUATION_MIN_INTERVIEWS: int = int(os.getenv('EVALUATION_MIN_INTERVIEWS', '1'))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration values are set
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_vars = [
            'AWS_REGION',
            'BEDROCK_MODEL_ID',
            'CANDIDATES_TABLE',
            'JOBS_TABLE',
            'INTERACTIONS_TABLE',
            'AGENT_STATE_TABLE'
        ]
        
        for var in required_vars:
            if not getattr(cls, var):
                return False
        
        return True
    
    @classmethod
    def get_table_names(cls) -> dict:
        """Get all DynamoDB table names as a dictionary"""
        return {
            'candidates': cls.CANDIDATES_TABLE,
            'jobs': cls.JOBS_TABLE,
            'interactions': cls.INTERACTIONS_TABLE,
            'agent_state': cls.AGENT_STATE_TABLE
        }
    
    @classmethod
    def get_bedrock_config(cls) -> dict:
        """Get Bedrock model configuration as a dictionary"""
        return {
            'model_id': cls.BEDROCK_MODEL_ID,
            'max_tokens': cls.MAX_TOKENS,
            'temperature': cls.TEMPERATURE,
            'top_p': cls.TOP_P
        }
    
    @classmethod
    def calculate_cost(cls, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for a Bedrock invocation
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            float: Cost in USD
        """
        input_cost = (input_tokens / 1000) * cls.COST_PER_1K_INPUT_TOKENS
        output_cost = (output_tokens / 1000) * cls.COST_PER_1K_OUTPUT_TOKENS
        return input_cost + output_cost
