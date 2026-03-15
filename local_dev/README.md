# Local Development Environment

Complete local testing environment for the Talent Acquisition Accelerator system. Run the entire multi-agent workflow without AWS costs.

## Overview

This directory contains mock services that simulate AWS infrastructure:

- **mock_bedrock.py** - Simulates Amazon Bedrock Nova API responses
- **mock_dynamodb.py** - In-memory DynamoDB implementation
- **mock_lambda.py** - Local Lambda function invocation
- **local_runner.py** - Complete workflow orchestration
- **test_scenarios.json** - Pre-configured test scenarios

## Quick Start

### 1. Run Complete Workflow

```bash
# Run with sample job data
python local_dev/local_runner.py \
  --job-file demo/01_sample_jobs.json \
  --job-index 0

# Run with step-by-step execution (pause after each agent)
python local_dev/local_runner.py \
  --job-file demo/01_sample_jobs.json \
  --job-index 0 \
  --step-by-step

# Run with test scenarios
python local_dev/local_runner.py \
  --job-file local_dev/test_scenarios.json \
  --job-index 0
```

### 2. Programmatic Usage

```python
from local_dev.local_runner import LocalRunner

# Initialize runner
runner = LocalRunner(verbose=True)

# Define job
job_data = {
    "title": "Senior Software Engineer",
    "description": "Build scalable systems...",
    "requirements": {
        "required_skills": ["Python", "AWS", "Docker"],
        "min_years_experience": 5
    }
}

# Run workflow
results = runner.run_workflow(job_data)

# Access results
print(f"Total candidates: {len(results['candidates'])}")
print(f"Total cost: ${results['metrics']['total_cost_usd']:.4f}")
```

## Mock Services

### Mock Bedrock

Simulates Nova API with realistic responses:

```python
from local_dev.mock_bedrock import get_mock_bedrock_client

client = get_mock_bedrock_client(latency_ms=500)
response = client.converse(
    modelId='amazon.nova-lite-v1:0',
    messages=[{
        "role": "user",
        "content": [{"text": "Generate candidate profile"}]
    }]
)

print(response['output']['message']['content'][0]['text'])
print(f"Tokens: {response['usage']['totalTokens']}")
```

### Mock DynamoDB

In-memory database with full CRUD operations:

```python
from local_dev.mock_dynamodb import get_mock_dynamodb_resource

dynamodb = get_mock_dynamodb_resource()
table = dynamodb.Table('talent-acq-candidates')

# Put item
table.put_item(Item={
    'candidateId': 'cand-123',
    'name': 'John Doe',
    'skills': ['Python', 'AWS']
})

# Get item
response = table.get_item(Key={'candidateId': 'cand-123'})
print(response['Item'])

# Reset data
dynamodb.reset()
```

### Mock Lambda

Local agent invocation:

```python
from local_dev.mock_lambda import get_mock_lambda_client
import json

client = get_mock_lambda_client(use_mock_services=True)

response = client.invoke(
    FunctionName='supervisor-agent',
    Payload=json.dumps({
        'operation': 'start_workflow',
        'jobId': 'job-123'
    })
)

result = json.loads(response['Payload'].read())
print(result)
```

## Test Scenarios

Three pre-configured scenarios in `test_scenarios.json`:

1. **Software Engineer - High Volume** (100 candidates expected)
2. **Data Scientist - Specialized** (50 candidates, specific skills)
3. **Product Manager - Leadership** (30 candidates, senior role)

Run specific scenario:

```bash
python local_dev/local_runner.py \
  --job-file local_dev/test_scenarios.json \
  --job-index 0  # 0, 1, or 2
```

## Output

Workflow execution produces:

1. **Console logs** - Real-time progress and metrics
2. **Results file** - JSON file with complete results (`results_YYYYMMDD_HHMMSS.json`)

### Results Structure

```json
{
  "state": {
    "stateId": "state-xxx",
    "workflowStatus": "completed",
    "agentsExecuted": ["sourcing", "screening", ...],
    "totalCostUsd": 0.0234
  },
  "candidates": [
    {
      "candidateId": "cand-xxx",
      "name": "Sarah Chen",
      "overallScore": 0.89,
      "status": "screened"
    }
  ],
  "metrics": {
    "total_cost_usd": 0.0234,
    "total_input_tokens": 1250,
    "total_output_tokens": 890,
    "execution_times": {
      "supervisor-agent": 0.52,
      "sourcing-agent": 2.34
    }
  }
}
```

## Validation Checklist

Before AWS deployment, verify locally:

- [ ] All 5 agents execute successfully
- [ ] Candidates are sourced and scored
- [ ] Screening filters candidates correctly
- [ ] Outreach messages are personalized
- [ ] Scheduling finds optimal slots
- [ ] Evaluation generates recommendations
- [ ] Cost tracking works correctly
- [ ] Error handling is robust
- [ ] Workflow completes end-to-end

## Troubleshooting

### Import Errors

```bash
# Ensure you're in project root
cd talent-acquisition-accelerator

# Install dependencies
pip install -r requirements.txt

# Run from project root
python local_dev/local_runner.py --job-file demo/01_sample_jobs.json --job-index 0
```

### Agent Failures

Check logs for specific error messages. Common issues:

- Missing required fields in job data
- Invalid JSON in payload
- Agent logic errors (check agent code)

### Mock Service Issues

Reset mock services:

```python
from local_dev.mock_dynamodb import mock_dynamodb_resource
mock_dynamodb_resource.reset()
```

## Performance Expectations

Local execution times (approximate):

- Supervisor initialization: < 1s
- Sourcing Agent: 2-5s (depends on candidate count)
- Screening Agent: 3-8s (depends on candidate count)
- Outreach Agent: 2-4s
- Scheduling Agent: 1-3s
- Evaluation Agent: 2-4s

**Total workflow: 10-25 seconds**

## Cost Simulation

Mock Bedrock simulates token usage:
- Input tokens: ~4 chars per token
- Output tokens: ~4 chars per token
- Cost: $0.00006 per 1K input, $0.00024 per 1K output

Typical workflow cost (simulated): **$0.02 - $0.05**

## Next Steps

After local validation:

1. Review results and verify quality
2. Adjust agent parameters if needed
3. Test with different job types
4. Proceed to Phase 5: AWS Deployment

## References

- 17_testing_strategy.md - Testing approach
- 16_module_build_checklist.md - Phase 3 requirements
- 14_cost_optimization_strategy.md - Cost management
