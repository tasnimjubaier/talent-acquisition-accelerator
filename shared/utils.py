"""
Shared Utility Functions for Talent Acquisition Accelerator

Core utilities for Bedrock invocation, DynamoDB operations, logging,
error handling, and cost tracking used across all agents.

References:
- 02_tech_stack_decisions.md: Technology stack and cost optimization
- 16_module_build_checklist.md: Phase 2 implementation requirements
- 13_security_architecture.md: Security best practices

Verification Sources:
- AWS Lambda Best Practices: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
- Amazon Bedrock API: https://docs.aws.amazon.com/bedrock/latest/userguide/api-methods-run.html
- DynamoDB Best Practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html
"""

import json
import logging
import time
from typing import Any, Dict, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from shared.config import Config

# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger()
logger.setLevel(Config.LOG_LEVEL)

# ============================================================================
# AWS Client Initialization
# Reference: Reuse connections for better Lambda performance
# Source: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
# ============================================================================

# Initialize clients outside handler for connection reuse
dynamodb = boto3.resource('dynamodb', region_name=Config.AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=Config.AWS_REGION)


# ============================================================================
# Bedrock / Nova Integration
# ============================================================================

def invoke_bedrock(
    prompt: str,
    system_prompt: Optional[str] = None,
    model_id: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None
) -> Dict[str, Any]:
    """
    Invoke Amazon Bedrock Nova model with error handling and retries
    
    This function handles:
    - Exponential backoff for throttling
    - Token usage tracking
    - Cost calculation
    - Error handling and logging
    
    Args:
        prompt: User prompt/question
        system_prompt: Optional system prompt for context
        model_id: Bedrock model ID (defaults to Config.BEDROCK_MODEL_ID)
        max_tokens: Maximum tokens to generate (defaults to Config.MAX_TOKENS)
        temperature: Sampling temperature (defaults to Config.TEMPERATURE)
        top_p: Nucleus sampling parameter (defaults to Config.TOP_P)
        
    Returns:
        Dict containing:
            - success (bool): Whether invocation succeeded
            - content (str): Generated text (if successful)
            - input_tokens (int): Number of input tokens used
            - output_tokens (int): Number of output tokens generated
            - cost_usd (float): Cost of this invocation in USD
            - latency (float): Response time in seconds
            - error (str): Error message (if failed)
            
    Example:
        >>> result = invoke_bedrock("Summarize this resume: ...")
        >>> if result['success']:
        >>>     print(result['content'])
        >>>     print(f"Cost: ${result['cost_usd']:.4f}")
    
    Verification Source:
    - Amazon Bedrock Converse API: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
    """
    # Use defaults from config if not specified
    model_id = model_id or Config.BEDROCK_MODEL_ID
    max_tokens = max_tokens or Config.MAX_TOKENS
    temperature = temperature or Config.TEMPERATURE
    top_p = top_p or Config.TOP_P
    
    # Build messages array
    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]
    
    # Build request body
    request_body = {
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p
        }
    }
    
    # Add system prompt if provided
    if system_prompt:
        request_body["system"] = [{"text": system_prompt}]
    
    # Retry loop with exponential backoff
    for attempt in range(Config.MAX_RETRIES):
        try:
            start_time = time.time()
            
            # Invoke Bedrock using Converse API
            response = bedrock_runtime.converse(
                modelId=model_id,
                **request_body
            )
            
            latency = time.time() - start_time
            
            # Extract response content
            output_message = response.get('output', {}).get('message', {})
            content_blocks = output_message.get('content', [])
            content = content_blocks[0].get('text', '') if content_blocks else ''
            
            # Extract token usage
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            
            # Calculate cost
            cost_usd = Config.calculate_cost(input_tokens, output_tokens)
            
            logger.info(
                f"Bedrock invocation successful: "
                f"{input_tokens} input tokens, {output_tokens} output tokens, "
                f"${cost_usd:.4f} cost, {latency:.2f}s latency"
            )
            
            return {
                'success': True,
                'content': content,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost_usd,
                'latency': latency,
                'model_id': model_id
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # Handle throttling with exponential backoff
            if error_code == 'ThrottlingException' and attempt < Config.MAX_RETRIES - 1:
                wait_time = Config.RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Bedrock throttled (attempt {attempt + 1}/{Config.MAX_RETRIES}), "
                    f"retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                continue
            
            # Log error and return failure
            logger.error(f"Bedrock invocation failed: {error_code} - {error_message}")
            return {
                'success': False,
                'error': error_message,
                'error_code': error_code
            }
            
        except BotoCoreError as e:
            logger.error(f"Boto3 error invoking Bedrock: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'BotoCoreError'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UnexpectedError'
            }
    
    # Max retries exceeded
    logger.error(f"Bedrock invocation failed after {Config.MAX_RETRIES} attempts")
    return {
        'success': False,
        'error': 'Max retries exceeded',
        'error_code': 'MaxRetriesExceeded'
    }



# ============================================================================
# DynamoDB Operations
# ============================================================================

def save_to_dynamodb(
    table_name: str,
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save item to DynamoDB with error handling
    
    Args:
        table_name: DynamoDB table name
        item: Item to save (dict)
        
    Returns:
        Dict with success status and error if applicable
        
    Example:
        >>> result = save_to_dynamodb('talent-acq-candidates', candidate_dict)
        >>> if result['success']:
        >>>     print("Candidate saved successfully")
    
    Verification Source:
    - DynamoDB PutItem: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_PutItem.html
    """
    try:
        table = dynamodb.Table(table_name)
        table.put_item(Item=item)
        
        logger.info(f"Successfully saved item to {table_name}")
        return {'success': True}
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Failed to save to DynamoDB: {error_code} - {error_message}")
        return {
            'success': False,
            'error': error_message,
            'error_code': error_code
        }
        
    except Exception as e:
        logger.error(f"Unexpected error saving to DynamoDB: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_code': 'UnexpectedError'
        }


def get_from_dynamodb(
    table_name: str,
    key: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Retrieve item from DynamoDB
    
    Args:
        table_name: DynamoDB table name
        key: Primary key (dict with partition key and optional sort key)
        
    Returns:
        Item if found, None otherwise
        
    Example:
        >>> item = get_from_dynamodb('talent-acq-jobs', {'jobId': 'job-123'})
        >>> if item:
        >>>     print(item['title'])
    
    Verification Source:
    - DynamoDB GetItem: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GetItem.html
    """
    try:
        table = dynamodb.Table(table_name)
        response = table.get_item(Key=key)
        
        item = response.get('Item')
        if item:
            logger.info(f"Successfully retrieved item from {table_name}")
        else:
            logger.warning(f"Item not found in {table_name} with key {key}")
        
        return item
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Failed to get from DynamoDB: {error_code} - {error_message}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error getting from DynamoDB: {str(e)}")
        return None


def update_dynamodb_item(
    table_name: str,
    key: Dict[str, Any],
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update item in DynamoDB
    
    Args:
        table_name: DynamoDB table name
        key: Primary key
        updates: Dictionary of attributes to update
        
    Returns:
        Dict with success status
        
    Example:
        >>> result = update_dynamodb_item(
        >>>     'talent-acq-candidates',
        >>>     {'candidateId': 'cand-123'},
        >>>     {'status': 'screened', 'screeningScore': 0.85}
        >>> )
    
    Verification Source:
    - DynamoDB UpdateItem: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateItem.html
    """
    try:
        table = dynamodb.Table(table_name)
        
        # Build update expression
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for i, (attr, value) in enumerate(updates.items()):
            placeholder = f":val{i}"
            name_placeholder = f"#attr{i}"
            
            if i > 0:
                update_expression += ", "
            
            update_expression += f"{name_placeholder} = {placeholder}"
            expression_attribute_values[placeholder] = value
            expression_attribute_names[name_placeholder] = attr
        
        # Add updatedAt timestamp
        update_expression += ", #updatedAt = :updatedAt"
        expression_attribute_names['#updatedAt'] = 'updatedAt'
        expression_attribute_values[':updatedAt'] = int(datetime.now().timestamp())
        
        table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
        )
        
        logger.info(f"Successfully updated item in {table_name}")
        return {'success': True}
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Failed to update DynamoDB: {error_code} - {error_message}")
        return {
            'success': False,
            'error': error_message,
            'error_code': error_code
        }
        
    except Exception as e:
        logger.error(f"Unexpected error updating DynamoDB: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_code': 'UnexpectedError'
        }


def query_dynamodb(
    table_name: str,
    key_condition_expression: str,
    expression_attribute_values: Dict[str, Any],
    index_name: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Query DynamoDB table or index
    
    Args:
        table_name: DynamoDB table name
        key_condition_expression: Query condition (e.g., "jobId = :jobId")
        expression_attribute_values: Values for placeholders (e.g., {":jobId": "job-123"})
        index_name: Optional GSI name
        limit: Optional result limit
        
    Returns:
        List of items matching query
        
    Example:
        >>> candidates = query_dynamodb(
        >>>     'talent-acq-candidates',
        >>>     'jobId = :jobId',
        >>>     {':jobId': 'job-123'},
        >>>     index_name='JobIdIndex'
        >>> )
    
    Verification Source:
    - DynamoDB Query: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Query.html
    """
    try:
        table = dynamodb.Table(table_name)
        
        query_params = {
            'KeyConditionExpression': key_condition_expression,
            'ExpressionAttributeValues': expression_attribute_values
        }
        
        if index_name:
            query_params['IndexName'] = index_name
        
        if limit:
            query_params['Limit'] = limit
        
        response = table.query(**query_params)
        items = response.get('Items', [])
        
        logger.info(f"Query returned {len(items)} items from {table_name}")
        return items
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Failed to query DynamoDB: {error_code} - {error_message}")
        return []
        
    except Exception as e:
        logger.error(f"Unexpected error querying DynamoDB: {str(e)}")
        return []



# ============================================================================
# Helper Utilities
# ============================================================================

def generate_id(prefix: str = "") -> str:
    """
    Generate unique ID with optional prefix
    
    Args:
        prefix: Optional prefix (e.g., "job-", "cand-")
        
    Returns:
        Unique ID string
        
    Example:
        >>> job_id = generate_id("job-")
        >>> # Returns: "job-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    import uuid
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id


def get_timestamp() -> int:
    """
    Get current Unix timestamp
    
    Returns:
        Current timestamp as integer
    """
    return int(datetime.now().timestamp())


def format_error_response(
    error: str,
    context: Optional[Dict] = None,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format standardized error response
    
    Args:
        error: Error message
        context: Optional context information
        error_code: Optional error code
        
    Returns:
        Standardized error response dict
    """
    return {
        'status': 'error',
        'error': error,
        'error_code': error_code,
        'context': context or {},
        'timestamp': get_timestamp()
    }


def format_success_response(
    data: Any,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Format standardized success response
    
    Args:
        data: Response data
        metadata: Optional metadata
        
    Returns:
        Standardized success response dict
    """
    return {
        'status': 'success',
        'data': data,
        'metadata': metadata or {},
        'timestamp': get_timestamp()
    }


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str]
) -> Optional[str]:
    """
    Validate that required fields are present in data
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Error message if validation fails, None if successful
        
    Example:
        >>> error = validate_required_fields(
        >>>     {'name': 'John', 'email': 'john@example.com'},
        >>>     ['name', 'email', 'phone']
        >>> )
        >>> if error:
        >>>     print(f"Validation failed: {error}")
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage safely (handles division by zero)
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    
    return (part / total) * 100


# ============================================================================
# Cost Tracking Utilities
# ============================================================================

def track_agent_cost(
    agent_name: str,
    input_tokens: int,
    output_tokens: int,
    state_id: str
) -> Dict[str, Any]:
    """
    Track cost for an agent execution and update agent state
    
    Args:
        agent_name: Name of the agent
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        state_id: Agent state ID to update
        
    Returns:
        Dict with cost information
    """
    cost_usd = Config.calculate_cost(input_tokens, output_tokens)
    
    logger.info(
        f"Agent {agent_name} cost: ${cost_usd:.4f} "
        f"({input_tokens} input + {output_tokens} output tokens)"
    )
    
    # Update agent state with cost tracking
    try:
        update_result = update_dynamodb_item(
            Config.AGENT_STATE_TABLE,
            {'stateId': state_id},
            {
                'totalInputTokens': input_tokens,
                'totalOutputTokens': output_tokens,
                'totalCostUsd': cost_usd
            }
        )
        
        if not update_result['success']:
            logger.warning(f"Failed to update cost tracking in agent state: {update_result.get('error')}")
    
    except Exception as e:
        logger.warning(f"Error updating cost tracking: {str(e)}")
    
    return {
        'agent_name': agent_name,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cost_usd': cost_usd
    }


def check_budget_alert(current_cost: float) -> bool:
    """
    Check if current cost exceeds budget alert threshold
    
    Args:
        current_cost: Current total cost in USD
        
    Returns:
        True if alert threshold exceeded, False otherwise
    """
    threshold_cost = Config.MONTHLY_BUDGET_USD * Config.BUDGET_ALERT_THRESHOLD
    
    if current_cost >= threshold_cost:
        logger.warning(
            f"Budget alert: Current cost ${current_cost:.2f} exceeds "
            f"{Config.BUDGET_ALERT_THRESHOLD * 100}% of monthly budget "
            f"(${Config.MONTHLY_BUDGET_USD:.2f})"
        )
        return True
    
    return False


# ============================================================================
# Logging Utilities
# ============================================================================

def log_agent_execution(
    agent_name: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO"
) -> None:
    """
    Log agent execution with structured format
    
    Args:
        agent_name: Name of the agent
        action: Action being performed
        details: Optional additional details
        level: Log level (INFO, WARNING, ERROR)
    """
    log_message = f"[{agent_name}] {action}"
    
    if details:
        log_message += f" | {json.dumps(details)}"
    
    if level == "INFO":
        logger.info(log_message)
    elif level == "WARNING":
        logger.warning(log_message)
    elif level == "ERROR":
        logger.error(log_message)
    else:
        logger.debug(log_message)


def log_performance_metrics(
    operation: str,
    duration: float,
    success: bool,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log performance metrics for operations
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        success: Whether operation succeeded
        metadata: Optional metadata
    """
    status = "SUCCESS" if success else "FAILED"
    log_message = f"[PERFORMANCE] {operation} | {status} | {duration:.2f}s"
    
    if metadata:
        log_message += f" | {json.dumps(metadata)}"
    
    logger.info(log_message)
