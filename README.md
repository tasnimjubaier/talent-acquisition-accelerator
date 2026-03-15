# Talent Acquisition Accelerator

**AI-Powered Multi-Agent Recruiting System**

Built with Amazon Nova, AWS Lambda, and CrewAI for the Amazon Nova Hackathon 2026.

## Overview

An intelligent recruiting automation system that uses 5 specialized AI agents to streamline the entire hiring pipeline from candidate sourcing to final evaluation.

## Architecture

- **Supervisor Agent**: Orchestrates the recruiting workflow
- **Sourcing Agent**: Finds and ranks candidates
- **Screening Agent**: Evaluates resumes and qualifications
- **Outreach Agent**: Generates personalized messages
- **Scheduling Agent**: Optimizes interview scheduling
- **Evaluation Agent**: Synthesizes feedback and recommendations

## Tech Stack

- **AI Model**: Amazon Nova 2 Lite (via Amazon Bedrock)
- **Framework**: CrewAI for multi-agent orchestration
- **Compute**: AWS Lambda (Python 3.12)
- **Database**: Amazon DynamoDB
- **API**: Amazon API Gateway

## Project Status

✅ **Phase 5.2: API Gateway Setup** - Complete

See [Development Roadmap](../00_governing_docs/15_development_roadmap.md) for detailed build plan.

## Quick Start

### Prerequisites

- AWS Account with Bedrock access
- AWS CLI configured
- Python 3.12+
- jq (for JSON parsing in scripts)

### Setup

1. Clone the repository
2. Run infrastructure setup scripts in order:
   ```bash
   cd infrastructure
   ./00_setup_aws.sh
   ./03_create_iam_roles.sh
   ./04_create_dynamodb_tables.sh
   ./11_deploy_all_agents.sh
   ./12_create_api_gateway.sh
   ```

3. Test the API:
   ```bash
   ./13_test_api_endpoint.sh
   ```

## API Usage

### Endpoint

After running the setup scripts, your API endpoint will be available at:
```
https://{api-id}.execute-api.us-east-1.amazonaws.com/workflow
```

The exact endpoint URL is saved in `infrastructure/api_gateway_config.json` after running `12_create_api_gateway.sh`.

### Authentication

Currently uses AWS IAM for Lambda invocation. API Gateway endpoint is publicly accessible for demo purposes.

### Request Format

**Endpoint:** `POST /workflow`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "jobId": "unique-job-id",
  "jobTitle": "Job Title",
  "jobDescription": "Detailed job description",
  "requiredSkills": ["Skill 1", "Skill 2", "Skill 3"],
  "location": "Job Location",
  "experienceLevel": "Entry|Mid-Level|Senior|Executive"
}
```

**Example Request:**
```bash
curl -X POST https://{api-id}.execute-api.us-east-1.amazonaws.com/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "job-001",
    "jobTitle": "Senior Software Engineer",
    "jobDescription": "Looking for experienced backend engineer with Python and AWS expertise",
    "requiredSkills": ["Python", "AWS", "Docker", "REST APIs"],
    "location": "Remote",
    "experienceLevel": "Senior"
  }'
```

### Response Format

**Success Response (HTTP 200):**
```json
{
  "status": "success",
  "workflowId": "workflow-uuid",
  "jobId": "job-001",
  "timestamp": 1710432000,
  "results": {
    "sourcing": {
      "candidatesFound": 50,
      "topCandidates": 10
    },
    "screening": {
      "candidatesScreened": 10,
      "qualified": 5
    },
    "outreach": {
      "messagesSent": 5
    },
    "scheduling": {
      "interviewsScheduled": 3
    },
    "evaluation": {
      "recommendations": ["candidate-1", "candidate-2"]
    }
  },
  "metadata": {
    "totalDuration": 25.3,
    "agentsInvoked": 5
  }
}
```

**Error Response (HTTP 400/500):**
```json
{
  "status": "error",
  "error": "Error message",
  "context": {
    "jobId": "job-001"
  },
  "timestamp": 1710432000
}
```

### Testing

Use the provided test script:
```bash
cd infrastructure
./13_test_api_endpoint.sh
```

This will run multiple test scenarios including:
- CORS preflight checks
- Error handling validation
- Software engineer hiring workflow
- Nurse hiring workflow
- Performance benchmarking

## Documentation

Full documentation available in `00_governing_docs/` directory:
- [Project Charter](../00_governing_docs/01_project_charter.md)
- [System Architecture](../00_governing_docs/07_system_architecture.md)
- [Agent Specifications](../00_governing_docs/08_agent_specifications.md)
- [Development Roadmap](../00_governing_docs/15_development_roadmap.md)

## License

MIT License - See LICENSE file for details.

## Hackathon

Built for Amazon Nova Hackathon 2026 #AmazonNova
