# Shared Utilities

Common utilities and helper functions used across all agents.

## Modules

### `config.py` - Configuration Management
- Environment variable handling with defaults
- AWS service configuration (region, account ID)
- DynamoDB table names
- Bedrock/Nova model configuration
- Agent-specific settings
- Cost tracking constants
- Helper methods for validation and cost calculation

### `models.py` - Data Models
- **Job** - Job posting with requirements and status tracking
- **Candidate** - Candidate profile with scoring and pipeline status
- **Interaction** - Candidate interactions (outreach, screening, interviews)
- **AgentState** - Workflow state and execution tracking
- **Enums** - JobStatus, CandidateStatus, InteractionType
- DynamoDB conversion helpers

### `utils.py` - Utility Functions

**Bedrock Integration:**
- `invoke_bedrock()` - Invoke Nova models with retry logic and cost tracking

**DynamoDB Operations:**
- `save_to_dynamodb()` - Save items with error handling
- `get_from_dynamodb()` - Retrieve items by key
- `update_dynamodb_item()` - Update items with automatic timestamps
- `query_dynamodb()` - Query tables and indexes

**Helper Functions:**
- `generate_id()` - Generate unique IDs with prefixes
- `get_timestamp()` - Get current Unix timestamp
- `format_error_response()` - Standardized error responses
- `format_success_response()` - Standardized success responses
- `validate_required_fields()` - Field validation
- `truncate_text()` - Text truncation
- `calculate_percentage()` - Safe percentage calculation

**Cost Tracking:**
- `track_agent_cost()` - Track and log agent execution costs
- `check_budget_alert()` - Monitor budget thresholds

**Logging:**
- `log_agent_execution()` - Structured agent logging
- `log_performance_metrics()` - Performance metric logging

## Usage Examples

### Invoke Bedrock
```python
from shared import invoke_bedrock

result = invoke_bedrock(
    prompt="Analyze this resume...",
    system_prompt="You are a recruiting assistant.",
    max_tokens=1000
)

if result['success']:
    print(result['content'])
    print(f"Cost: ${result['cost_usd']:.4f}")
```

### Save to DynamoDB
```python
from shared import Candidate, save_to_dynamodb, Config

candidate = Candidate(
    job_id="job-123",
    name="John Doe",
    email="john@example.com",
    skills=["Python", "AWS"]
)

result = save_to_dynamodb(
    Config.CANDIDATES_TABLE,
    candidate.to_dynamodb_item()
)
```

### Query Candidates
```python
from shared import query_dynamodb, Config

candidates = query_dynamodb(
    Config.CANDIDATES_TABLE,
    'jobId = :jobId',
    {':jobId': 'job-123'},
    index_name='JobIdIndex'
)
```

## Testing

Run unit tests:
```bash
pytest tests/test_utils.py -v --cov=shared
```

Test Bedrock connection:
```bash
python infrastructure/08_test_bedrock_connection.py
```

## Status

✅ Phase 2: Core Services Setup - COMPLETE

All core services implemented, tested, and verified.
