# Learning and Codebase Mastery System

**Purpose**: Complete pathway to understand the Talent Acquisition Accelerator system from fundamentals to deep architectural mastery.

**Target Audience**: You (developer learning this codebase)

**Time Investment**: 7-10 days for full mastery

**Verification Sources**: All claims link to official documentation

---

## Table of Contents

1. [System Overview & Learning Philosophy](#1-system-overview--learning-philosophy)
2. [Prerequisites Check](#2-prerequisites-check)
3. [Technology Deep-Dives](#3-technology-deep-dives)
4. [Hands-On Labs](#4-hands-on-labs)
5. [Codebase Architecture Map](#5-codebase-architecture-map)
6. [Module-by-Module Reading Guide](#6-module-by-module-reading-guide)
7. [Integration Flows & Data Paths](#7-integration-flows--data-paths)
8. [Verification Checkpoints](#8-verification-checkpoints)
9. [Reference Library](#9-reference-library)
10. [Troubleshooting Guide](#10-troubleshooting-guide)

---

## 1. System Overview & Learning Philosophy

### What You're Building

A multi-agent AI system that accelerates talent acquisition by:
- Parsing job descriptions (JD Parser Agent)
- Sourcing candidates (Candidate Sourcer Agent)
- Screening resumes (Resume Screener Agent)
- Conducting initial assessments (Interview Agent)
- Generating reports (Report Generator Agent)
- Orchestrating the entire workflow (Supervisor Agent)

### Learning Philosophy

**Bottom-Up Approach**: Understand infrastructure → services → agents → orchestration

**Hands-On First**: Experiment with isolated components before reading production code

**Verify Everything**: Every technology claim links to official docs

**Iterate & Test**: Complete checkpoints to validate understanding

### Learning Stages

**Stage 1: Foundation** (Days 1-3)
- AWS fundamentals (Lambda, DynamoDB, IAM, Bedrock)
- Python async patterns
- AI agent concepts

**Stage 2: Technology Mastery** (Days 3-5)
- CrewAI framework deep-dive
- Amazon Nova models
- Integration patterns

**Stage 3: Codebase Understanding** (Days 5-8)
- Architecture overview
- Module dependencies
- Code reading sequence

**Stage 4: Integration Mastery** (Days 8-10)
- Data flow tracing
- Agent communication
- End-to-end workflows

---

## 2. Prerequisites Check

### Required Knowledge

✅ **Python 3.x basics**
- Functions, classes, decorators
- Exception handling
- Type hints
- Async/await (will deep-dive here)

✅ **Basic AWS concepts**
- Cloud computing fundamentals
- Serverless architecture concept
- API concepts (REST, JSON)

✅ **Git basics**
- Clone, commit, branch
- Reading code on GitHub

### Knowledge Gaps (We'll Fill)

❌ AWS Lambda internals
❌ DynamoDB data modeling
❌ CrewAI framework
❌ Amazon Bedrock/Nova
❌ Multi-agent orchestration
❌ Serverless deployment

### Tools Setup

**Required**:
- Python 3.12+ installed
- AWS CLI configured
- Code editor (VS Code recommended)
- Git

**Verification**:
```bash
python --version  # Should be 3.12+
aws --version     # Should be installed
git --version     # Should be installed
```

---

## 3. Technology Deep-Dives

### 3.1 AWS Lambda

**What It Is**: Serverless compute service that runs code in response to events without managing servers.

**Official Docs**: https://docs.aws.amazon.com/lambda/latest/dg/welcome.html

**Key Concepts**:

1. **Handler Function**: Entry point for Lambda execution
```python
def lambda_handler(event, context):
    # event: input data (dict)
    # context: runtime information
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda'
    }
```

2. **Event Structure**: Input data passed to your function
```python
# API Gateway event example
{
    'body': '{"key": "value"}',
    'headers': {'Content-Type': 'application/json'},
    'httpMethod': 'POST',
    'path': '/api/endpoint'
}
```

3. **Context Object**: Runtime info (request ID, memory limit, remaining time)
```python
context.aws_request_id      # Unique request ID
context.function_name       # Lambda function name
context.memory_limit_in_mb  # Allocated memory
context.get_remaining_time_in_millis()  # Time left
```

4. **Cold Start vs Warm Start**:
- **Cold Start**: First invocation or after idle period (slower, ~1-3s)
- **Warm Start**: Subsequent invocations reuse container (faster, ~10-100ms)
- **Optimization**: Keep functions small, minimize dependencies

5. **Execution Environment**:
- Isolated container per function
- Temporary storage: `/tmp` (512MB-10GB)
- Environment variables for configuration
- Execution role for AWS permissions

**In Our System**:
- Each agent runs as a Lambda function
- Supervisor orchestrates agent invocations
- DynamoDB stores state between invocations
- Bedrock called from Lambda for AI inference

**Learn More**:
- Lambda execution model: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html
- Best practices: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html

---

### 3.2 Amazon DynamoDB

**What It Is**: Fully managed NoSQL database with single-digit millisecond performance at any scale.

**Official Docs**: https://docs.aws.amazon.com/dynamodb/

**Key Concepts**:

1. **Tables, Items, Attributes**:
```python
# Table: candidates
# Item (row):
{
    'candidate_id': '123',           # Partition key
    'timestamp': '2026-03-15T10:00', # Sort key
    'name': 'John Doe',
    'skills': ['Python', 'AWS'],
    'score': 85
}
```

2. **Primary Keys**:
- **Partition Key**: Unique identifier (e.g., `candidate_id`)
- **Composite Key**: Partition key + Sort key (e.g., `candidate_id` + `timestamp`)

3. **Indexes**:
- **GSI (Global Secondary Index)**: Query on non-key attributes
- **LSI (Local Secondary Index)**: Alternative sort key

4. **Read/Write Capacity**:
- **On-Demand**: Pay per request (good for unpredictable workloads)
- **Provisioned**: Set RCU/WCU (cheaper for predictable workloads)

5. **Operations**:
```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('candidates')

# Put item
table.put_item(Item={'candidate_id': '123', 'name': 'John'})

# Get item
response = table.get_item(Key={'candidate_id': '123'})
item = response['Item']

# Query (requires partition key)
response = table.query(
    KeyConditionExpression='candidate_id = :id',
    ExpressionAttributeValues={':id': '123'}
)

# Scan (reads entire table - expensive!)
response = table.scan(
    FilterExpression='score > :score',
    ExpressionAttributeValues={':score': 80}
)
```

**Data Modeling Best Practices**:
- Design for access patterns, not normalization
- Use composite keys for hierarchical data
- Avoid scans (use queries with indexes)
- Denormalize data (duplicate is OK)

**In Our System**:
- `job_descriptions` table: Stores parsed JDs
- `candidates` table: Stores candidate profiles
- `screening_results` table: Stores agent outputs
- `workflow_state` table: Tracks pipeline progress

**Learn More**:
- DynamoDB core concepts: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html
- Best practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html

---

### 3.3 Amazon Bedrock & Nova Models

**What It Is**: Fully managed service to build generative AI applications using foundation models via API.

**Official Docs**: https://docs.aws.amazon.com/bedrock/

**Key Concepts**:

1. **Foundation Models**: Pre-trained large language models
   - Amazon Nova (our choice): Fast, cost-effective
   - Claude, Llama, Mistral, etc.

2. **Model IDs**:
```python
# Nova 2 Lite (our model)
model_id = 'amazon.nova-lite-v1:0'

# Other options
# 'amazon.nova-pro-v1:0'  # More capable, slower
# 'anthropic.claude-3-sonnet-20240229-v1:0'  # Claude
```

3. **Inference API**:
```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

response = bedrock.invoke_model(
    modelId='amazon.nova-lite-v1:0',
    body=json.dumps({
        'prompt': 'Extract skills from this resume: ...',
        'max_tokens': 500,
        'temperature': 0.7,
        'top_p': 0.9
    })
)

result = json.loads(response['body'].read())
text = result['completion']
```

4. **Parameters**:
- `temperature`: Randomness (0=deterministic, 1=creative)
- `max_tokens`: Max output length
- `top_p`: Nucleus sampling (0.9 = top 90% probability mass)
- `stop_sequences`: Stop generation at specific strings

5. **Prompt Engineering**:
```python
# Good prompt structure
prompt = f"""
Task: Extract candidate skills from resume

Resume:
{resume_text}

Output format: JSON array of skills

Example: ["Python", "AWS", "Machine Learning"]

Skills:
"""
```

**Nova 2 Lite Specifics**:
- Speed: ~100-200ms latency
- Cost: $0.00006 per 1K input tokens, $0.00024 per 1K output tokens
- Context: 300K tokens input
- Best for: Classification, extraction, short generation

**In Our System**:
- JD Parser: Extracts requirements from job descriptions
- Resume Screener: Matches candidates to requirements
- Interview Agent: Generates assessment questions
- Report Generator: Creates hiring recommendations

**Learn More**:
- Bedrock user guide: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
- Nova models: https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html
- Prompt engineering: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-engineering-guidelines.html

---

### 3.4 CrewAI Framework

**What It Is**: Python framework for orchestrating role-playing autonomous AI agents.

**Official Docs**: https://docs.crewai.com/

**Key Concepts**:

1. **Agents**: Autonomous entities with roles, goals, and tools
```python
from crewai import Agent

agent = Agent(
    role='Resume Screener',
    goal='Match candidates to job requirements',
    backstory='Expert recruiter with 10 years experience',
    tools=[resume_parser_tool, scoring_tool],
    llm=bedrock_llm,
    verbose=True
)
```

2. **Tasks**: Specific assignments for agents
```python
from crewai import Task

task = Task(
    description='Screen 10 resumes for Senior Python Developer role',
    agent=screener_agent,
    expected_output='List of top 3 candidates with scores'
)
```

3. **Crews**: Teams of agents working together
```python
from crewai import Crew

crew = Crew(
    agents=[parser_agent, screener_agent, interviewer_agent],
    tasks=[parse_task, screen_task, interview_task],
    process='sequential'  # or 'hierarchical'
)

result = crew.kickoff()
```

4. **Tools**: Functions agents can use
```python
from crewai_tools import tool

@tool
def parse_resume(resume_text: str) -> dict:
    """Parse resume and extract structured data"""
    # Implementation
    return {'name': '...', 'skills': [...]}
```

5. **Process Types**:
- **Sequential**: Tasks run one after another
- **Hierarchical**: Manager agent delegates to workers

**In Our System**:
- 5 specialized agents (JD Parser, Sourcer, Screener, Interviewer, Reporter)
- 1 supervisor agent (orchestrates workflow)
- Each agent has specific tools and LLM access
- Hierarchical process with supervisor managing flow

**Learn More**:
- CrewAI concepts: https://docs.crewai.com/concepts/agents
- Tools guide: https://docs.crewai.com/concepts/tools
- Crews guide: https://docs.crewai.com/concepts/crews

---

### 3.5 Python Async Patterns

**What It Is**: Concurrent programming using `async`/`await` for I/O-bound operations.

**Official Docs**: https://docs.python.org/3/library/asyncio.html

**Key Concepts**:

1. **Async Functions**:
```python
async def fetch_data():
    # Simulates I/O operation
    await asyncio.sleep(1)
    return 'data'

# Call async function
result = await fetch_data()
```

2. **Running Async Code**:
```python
import asyncio

# In script
asyncio.run(fetch_data())

# In Lambda (already in event loop)
result = await fetch_data()
```

3. **Concurrent Execution**:
```python
# Run multiple tasks concurrently
results = await asyncio.gather(
    fetch_data_1(),
    fetch_data_2(),
    fetch_data_3()
)
```

4. **When to Use Async**:
- ✅ API calls (Bedrock, external APIs)
- ✅ Database queries (DynamoDB)
- ✅ File I/O
- ❌ CPU-intensive tasks (use multiprocessing)

**In Our System**:
- Async Bedrock calls for parallel inference
- Async DynamoDB operations
- Concurrent agent task execution

**Learn More**:
- Asyncio tutorial: https://docs.python.org/3/library/asyncio-task.html
- Real Python guide: https://realpython.com/async-io-python/

---


## 4. Hands-On Labs

### Lab 1: Hello Lambda

**Goal**: Create and test a simple Lambda function locally.

**Setup**:
```bash
mkdir lambda_lab && cd lambda_lab
touch lambda_function.py
```

**Code** (`lambda_function.py`):
```python
import json

def lambda_handler(event, context):
    """Simple Lambda that echoes input"""
    
    print(f"Received event: {json.dumps(event)}")
    
    # Extract data from event
    name = event.get('name', 'World')
    
    # Return response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'request_id': context.aws_request_id if context else 'local'
        })
    }

# Local testing
if __name__ == '__main__':
    # Mock event and context
    class MockContext:
        aws_request_id = 'test-123'
    
    test_event = {'name': 'Developer'}
    result = lambda_handler(test_event, MockContext())
    print(result)
```

**Run**:
```bash
python lambda_function.py
```

**Expected Output**:
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Hello, Developer!\", \"request_id\": \"test-123\"}"
}
```

**Checkpoint**:
- ✅ Understand event/context parameters
- ✅ Can return proper response structure
- ✅ Can test Lambda locally

---

### Lab 2: DynamoDB CRUD Operations

**Goal**: Perform create, read, update, delete operations on DynamoDB.

**Setup**:
```bash
pip install boto3
```

**Code** (`dynamodb_lab.py`):
```python
import boto3
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Create table (run once)
def create_table():
    table = dynamodb.create_table(
        TableName='candidates_lab',
        KeySchema=[
            {'AttributeName': 'candidate_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'candidate_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    print("Table created")

# CRUD operations
def crud_operations():
    table = dynamodb.Table('candidates_lab')
    
    # CREATE
    table.put_item(Item={
        'candidate_id': 'cand_001',
        'name': 'Alice Johnson',
        'skills': ['Python', 'AWS', 'Docker'],
        'experience_years': Decimal('5'),
        'created_at': datetime.now().isoformat()
    })
    print("✅ Created item")
    
    # READ
    response = table.get_item(Key={'candidate_id': 'cand_001'})
    item = response.get('Item')
    print(f"✅ Read item: {item['name']}")
    
    # UPDATE
    table.update_item(
        Key={'candidate_id': 'cand_001'},
        UpdateExpression='SET experience_years = :exp',
        ExpressionAttributeValues={':exp': Decimal('6')}
    )
    print("✅ Updated item")
    
    # DELETE
    table.delete_item(Key={'candidate_id': 'cand_001'})
    print("✅ Deleted item")

if __name__ == '__main__':
    # create_table()  # Run once
    crud_operations()
```

**Run**:
```bash
python dynamodb_lab.py
```

**Checkpoint**:
- ✅ Can create/read/update/delete items
- ✅ Understand key structure
- ✅ Know when to use Decimal for numbers

---

### Lab 3: Bedrock API Call

**Goal**: Make inference request to Amazon Nova model.

**Setup**:
```bash
pip install boto3
```

**Code** (`bedrock_lab.py`):
```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def call_nova(prompt: str) -> str:
    """Call Amazon Nova Lite model"""
    
    body = json.dumps({
        'prompt': prompt,
        'max_tokens': 200,
        'temperature': 0.7,
        'top_p': 0.9
    })
    
    response = bedrock.invoke_model(
        modelId='amazon.nova-lite-v1:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['completion']

# Test
if __name__ == '__main__':
    prompt = """
    Extract skills from this resume:
    
    John Doe - Senior Developer
    - 5 years Python experience
    - AWS certified
    - Built microservices with Docker
    
    Skills (JSON array):
    """
    
    skills = call_nova(prompt)
    print(f"Extracted skills: {skills}")
```

**Run**:
```bash
python bedrock_lab.py
```

**Expected Output**:
```
Extracted skills: ["Python", "AWS", "Docker", "Microservices"]
```

**Checkpoint**:
- ✅ Can call Bedrock API
- ✅ Understand prompt structure
- ✅ Can parse response

---

### Lab 4: CrewAI Simple Agent

**Goal**: Create a single agent that performs a task.

**Setup**:
```bash
pip install crewai crewai-tools
```

**Code** (`crewai_lab.py`):
```python
from crewai import Agent, Task, Crew
from crewai_tools import tool
import os

# Set OpenAI API key (CrewAI default LLM)
# For Bedrock, you'd configure custom LLM
os.environ['OPENAI_API_KEY'] = 'your-key-here'

# Define a tool
@tool
def calculate_score(skills: list, required_skills: list) -> int:
    """Calculate match score between candidate and job"""
    matches = len(set(skills) & set(required_skills))
    total = len(required_skills)
    return int((matches / total) * 100)

# Create agent
screener = Agent(
    role='Resume Screener',
    goal='Evaluate candidate fit for job requirements',
    backstory='Expert technical recruiter with pattern matching skills',
    tools=[calculate_score],
    verbose=True
)

# Create task
task = Task(
    description="""
    Evaluate this candidate:
    - Skills: Python, AWS, Docker, Kubernetes
    - Required: Python, AWS, React, TypeScript
    
    Use the calculate_score tool and provide recommendation.
    """,
    agent=screener,
    expected_output='Score and recommendation (proceed/reject)'
)

# Create crew
crew = Crew(
    agents=[screener],
    tasks=[task],
    verbose=True
)

# Execute
if __name__ == '__main__':
    result = crew.kickoff()
    print(f"\n=== Result ===\n{result}")
```

**Run**:
```bash
python crewai_lab.py
```

**Checkpoint**:
- ✅ Can create agent with role/goal
- ✅ Can define custom tools
- ✅ Understand task structure
- ✅ Can execute crew

---

### Lab 5: Multi-Agent Integration

**Goal**: Create two agents that work together sequentially.

**Code** (`multi_agent_lab.py`):
```python
from crewai import Agent, Task, Crew
from crewai_tools import tool

# Tool 1: Parse job description
@tool
def parse_jd(jd_text: str) -> dict:
    """Extract requirements from job description"""
    # Simplified parsing
    return {
        'title': 'Senior Python Developer',
        'required_skills': ['Python', 'AWS', 'Docker'],
        'experience_years': 5
    }

# Tool 2: Score candidate
@tool
def score_candidate(candidate_skills: list, required_skills: list) -> int:
    """Calculate match score"""
    matches = len(set(candidate_skills) & set(required_skills))
    return int((matches / len(required_skills)) * 100)

# Agent 1: JD Parser
parser = Agent(
    role='Job Description Parser',
    goal='Extract structured requirements from job postings',
    backstory='Expert at understanding hiring needs',
    tools=[parse_jd],
    verbose=True
)

# Agent 2: Screener
screener = Agent(
    role='Resume Screener',
    goal='Match candidates to job requirements',
    backstory='Technical recruiter with keen eye for talent',
    tools=[score_candidate],
    verbose=True
)

# Task 1: Parse JD
parse_task = Task(
    description='Parse this JD: "Looking for Senior Python Developer with AWS and Docker experience"',
    agent=parser,
    expected_output='Structured requirements (JSON)'
)

# Task 2: Screen candidate (depends on Task 1)
screen_task = Task(
    description="""
    Using requirements from previous task, evaluate candidate:
    - Skills: Python, AWS, Kubernetes, React
    
    Provide score and recommendation.
    """,
    agent=screener,
    expected_output='Score and recommendation'
)

# Create crew with sequential process
crew = Crew(
    agents=[parser, screener],
    tasks=[parse_task, screen_task],
    process='sequential',
    verbose=True
)

if __name__ == '__main__':
    result = crew.kickoff()
    print(f"\n=== Final Result ===\n{result}")
```

**Checkpoint**:
- ✅ Can create multi-agent workflow
- ✅ Understand task dependencies
- ✅ Can pass data between agents
- ✅ Understand sequential process

---

## 5. Codebase Architecture Map

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway / EventBridge               │
│                    (Entry point for requests)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Supervisor Agent (Lambda)                 │
│              Orchestrates entire workflow                   │
└─┬───────┬───────┬───────┬───────┬─────────────────────────┘
  │       │       │       │       │
  ▼       ▼       ▼       ▼       ▼
┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
│JD │   │Src│   │Scr│   │Int│   │Rep│  ← Agent Lambdas
│Par│   │cer│   │een│   │erv│   │ort│
└─┬─┘   └─┬─┘   └─┬─┘   └─┬─┘   └─┬─┘
  │       │       │       │       │
  └───────┴───────┴───────┴───────┘
                  │
                  ▼
         ┌────────────────┐
         │   DynamoDB     │  ← State storage
         │   - job_descriptions
         │   - candidates
         │   - screening_results
         │   - workflow_state
         └────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Amazon Bedrock │  ← AI inference
         │  (Nova Lite)   │
         └────────────────┘
```

### Directory Structure

```
talent-acquisition-accelerator/
├── infrastructure/          # AWS setup (CDK/Terraform)
│   ├── lambda_roles.py     # IAM roles for Lambdas
│   ├── dynamodb_tables.py  # Table definitions
│   └── api_gateway.py      # API endpoints
│
├── shared/                  # Common utilities
│   ├── bedrock_client.py   # Bedrock API wrapper
│   ├── dynamodb_client.py  # DynamoDB operations
│   ├── logger.py           # Logging setup
│   └── models.py           # Data models (Pydantic)
│
├── agents/                  # Agent implementations
│   ├── jd_parser/
│   │   ├── agent.py        # Agent definition
│   │   ├── tools.py        # Agent-specific tools
│   │   └── prompts.py      # Prompt templates
│   ├── candidate_sourcer/
│   ├── resume_screener/
│   ├── interview_agent/
│   ├── report_generator/
│   └── supervisor/
│
├── tests/                   # Unit and integration tests
│   ├── test_agents/
│   ├── test_shared/
│   └── test_integration/
│
├── docs/                    # Documentation
│   ├── 01_project_brief.md
│   ├── 02_tech_stack_decisions.md
│   └── ... (30 governing docs)
│
└── deployment/              # Deployment scripts
    ├── deploy.sh
    └── requirements.txt
```

### Module Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Supervisor│  │JD Parser │  │ Screener │  ... (agents)│
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
└───────┼─────────────┼─────────────┼───────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
┌─────────────────────┼─────────────────────────────────┐
│              Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │Bedrock Client│  │DynamoDB Client│  │Logger       │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
└────────────────────────────────────────────────────────┘
                      │
┌─────────────────────┼─────────────────────────────────┐
│           Infrastructure Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Lambda  │  │ DynamoDB │  │ Bedrock  │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└────────────────────────────────────────────────────────┘
```

**Dependency Rules**:
- Agents depend on shared services (not vice versa)
- Shared services depend on infrastructure (not vice versa)
- No circular dependencies between agents
- Supervisor can invoke agents, agents cannot invoke supervisor

---


## 6. Module-by-Module Reading Guide

### Reading Sequence

Follow this order to build understanding from bottom-up:

1. **Infrastructure Layer** (Days 1-2)
   - `infrastructure/dynamodb_tables.py`
   - `infrastructure/lambda_roles.py`
   - `infrastructure/api_gateway.py`

2. **Shared Services Layer** (Days 2-3)
   - `shared/models.py`
   - `shared/logger.py`
   - `shared/dynamodb_client.py`
   - `shared/bedrock_client.py`

3. **Agent Layer** (Days 4-6)
   - `agents/jd_parser/`
   - `agents/candidate_sourcer/`
   - `agents/resume_screener/`
   - `agents/interview_agent/`
   - `agents/report_generator/`

4. **Orchestration Layer** (Day 7)
   - `agents/supervisor/`

5. **Integration Tests** (Day 8)
   - `tests/test_integration/`

---

### 6.1 Infrastructure Layer

#### File: `infrastructure/dynamodb_tables.py`

**Purpose**: Define DynamoDB table schemas and indexes.

**What to Look For**:
- Table names and key structures
- GSI/LSI definitions
- Capacity modes (on-demand vs provisioned)

**Key Code Patterns**:
```python
# Table definition
{
    'TableName': 'job_descriptions',
    'KeySchema': [
        {'AttributeName': 'job_id', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'job_id', 'AttributeType': 'S'},
        {'AttributeName': 'created_at', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'created_at_index',
            'KeySchema': [
                {'AttributeName': 'created_at', 'KeyType': 'HASH'}
            ]
        }
    ]
}
```

**Questions to Answer**:
- What are the primary keys for each table?
- What queries will each GSI support?
- Why on-demand vs provisioned capacity?

**Verification**: Cross-reference with `05_data_models.md` in governing docs.

---

#### File: `infrastructure/lambda_roles.py`

**Purpose**: Define IAM roles and policies for Lambda functions.

**What to Look For**:
- Permissions for each agent
- Least privilege principle
- Resource-level permissions

**Key Code Patterns**:
```python
# Lambda execution role
{
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': [
                'dynamodb:GetItem',
                'dynamodb:PutItem',
                'dynamodb:Query'
            ],
            'Resource': 'arn:aws:dynamodb:*:*:table/candidates'
        },
        {
            'Effect': 'Allow',
            'Action': 'bedrock:InvokeModel',
            'Resource': 'arn:aws:bedrock:*:*:model/amazon.nova-lite-v1:0'
        }
    ]
}
```

**Questions to Answer**:
- What AWS services can each agent access?
- Are permissions scoped to specific resources?
- Why does supervisor need different permissions than agents?

**Verification**: AWS IAM best practices - https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

#### File: `infrastructure/api_gateway.py`

**Purpose**: Define API endpoints that trigger Lambda functions.

**What to Look For**:
- REST API routes
- Request/response transformations
- CORS configuration
- Authentication/authorization

**Key Code Patterns**:
```python
# API Gateway route
{
    'path': '/api/screen-candidates',
    'method': 'POST',
    'integration': {
        'type': 'AWS_PROXY',
        'uri': 'arn:aws:lambda:...:function:supervisor'
    },
    'cors': {
        'allowOrigins': ['*'],
        'allowMethods': ['POST', 'OPTIONS']
    }
}
```

**Questions to Answer**:
- What endpoints are exposed?
- How do requests reach the supervisor?
- What's the request/response format?

**Verification**: API Gateway docs - https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html

---

### 6.2 Shared Services Layer

#### File: `shared/models.py`

**Purpose**: Define data models using Pydantic for validation.

**What to Look For**:
- Data structures for each entity
- Validation rules
- Type hints
- Serialization methods

**Key Code Patterns**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class JobDescription(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    title: str
    required_skills: List[str]
    experience_years: int = Field(ge=0, le=50)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Candidate(BaseModel):
    candidate_id: str
    name: str
    skills: List[str]
    experience_years: int
    resume_text: str
    
    def to_dynamodb(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'candidate_id': self.candidate_id,
            'name': self.name,
            'skills': self.skills,
            'experience_years': self.experience_years
        }
```

**Questions to Answer**:
- What fields are required vs optional?
- What validation rules exist?
- How do models convert to/from DynamoDB?

**Verification**: Pydantic docs - https://docs.pydantic.dev/

---

#### File: `shared/logger.py`

**Purpose**: Centralized logging configuration for all Lambda functions.

**What to Look For**:
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Structured logging (JSON format)
- Context injection (request_id, agent_name)

**Key Code Patterns**:
```python
import logging
import json
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """Get configured logger for module"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # JSON formatter for CloudWatch
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    return logger

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'function': record.funcName
        }
        return json.dumps(log_data)
```

**Questions to Answer**:
- Why JSON format for logs?
- How to add context to logs?
- What log level for production?

**Verification**: Python logging docs - https://docs.python.org/3/library/logging.html

---

#### File: `shared/dynamodb_client.py`

**Purpose**: Wrapper around boto3 DynamoDB client with error handling and retries.

**What to Look For**:
- CRUD operation methods
- Error handling patterns
- Retry logic
- Batch operations

**Key Code Patterns**:
```python
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, List
import time

class DynamoDBClient:
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.logger = get_logger(__name__)
    
    def put_item(self, item: dict, retries: int = 3) -> bool:
        """Put item with exponential backoff retry"""
        for attempt in range(retries):
            try:
                self.table.put_item(Item=item)
                self.logger.info(f"Put item: {item.get('id')}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Throttled, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"DynamoDB error: {e}")
                    raise
        return False
    
    def get_item(self, key: dict) -> Optional[Dict]:
        """Get item by key"""
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            self.logger.error(f"Get item error: {e}")
            return None
    
    def query(self, key_condition: str, expression_values: dict) -> List[Dict]:
        """Query with pagination"""
        items = []
        last_key = None
        
        while True:
            params = {
                'KeyConditionExpression': key_condition,
                'ExpressionAttributeValues': expression_values
            }
            if last_key:
                params['ExclusiveStartKey'] = last_key
            
            response = self.table.query(**params)
            items.extend(response.get('Items', []))
            
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
        
        return items
```

**Questions to Answer**:
- Why retry logic for put_item?
- How does pagination work in query?
- When to use query vs scan?
- How are errors handled?

**Verification**: Boto3 DynamoDB docs - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html

---

#### File: `shared/bedrock_client.py`

**Purpose**: Wrapper around Bedrock API with prompt management and error handling.

**What to Look For**:
- Model invocation patterns
- Prompt templates
- Response parsing
- Token usage tracking
- Error handling

**Key Code Patterns**:
```python
import boto3
import json
from typing import Dict, Optional
from botocore.exceptions import ClientError

class BedrockClient:
    def __init__(self, model_id: str = 'amazon.nova-lite-v1:0'):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = model_id
        self.logger = get_logger(__name__)
    
    def invoke(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Optional[str]:
        """Invoke Bedrock model with prompt"""
        
        body = json.dumps({
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p
        })
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            result = json.loads(response['body'].read())
            completion = result.get('completion', '')
            
            # Log token usage
            input_tokens = result.get('input_tokens', 0)
            output_tokens = result.get('output_tokens', 0)
            self.logger.info(f"Tokens: {input_tokens} in, {output_tokens} out")
            
            return completion
            
        except ClientError as e:
            self.logger.error(f"Bedrock error: {e}")
            return None
    
    def invoke_with_template(
        self,
        template: str,
        variables: Dict[str, str],
        **kwargs
    ) -> Optional[str]:
        """Invoke with prompt template"""
        prompt = template.format(**variables)
        return self.invoke(prompt, **kwargs)
```

**Questions to Answer**:
- How are prompts structured?
- Why track token usage?
- How are API errors handled?
- What are default parameters?

**Verification**: Bedrock API reference - https://docs.aws.amazon.com/bedrock/latest/APIReference/welcome.html

---

### 6.3 Agent Layer

#### General Agent Structure

Each agent follows this pattern:
```
agents/<agent_name>/
├── agent.py       # CrewAI agent definition
├── tools.py       # Agent-specific tools
├── prompts.py     # Prompt templates
└── lambda_handler.py  # Lambda entry point
```

---

#### File: `agents/jd_parser/agent.py`

**Purpose**: Define JD Parser agent using CrewAI.

**What to Look For**:
- Agent role, goal, backstory
- Tools assigned to agent
- LLM configuration
- Agent behavior settings

**Key Code Patterns**:
```python
from crewai import Agent
from .tools import extract_requirements, parse_skills
from shared.bedrock_client import BedrockClient

def create_jd_parser_agent() -> Agent:
    """Create JD Parser agent"""
    
    bedrock_llm = BedrockClient(model_id='amazon.nova-lite-v1:0')
    
    agent = Agent(
        role='Job Description Parser',
        goal='Extract structured requirements from job postings',
        backstory="""You are an expert recruiter with 15 years of experience 
        analyzing job descriptions. You excel at identifying key requirements, 
        skills, and qualifications.""",
        tools=[extract_requirements, parse_skills],
        llm=bedrock_llm,
        verbose=True,
        allow_delegation=False  # Don't delegate to other agents
    )
    
    return agent
```

**Questions to Answer**:
- What is the agent's specific role?
- What tools does it have access to?
- Why `allow_delegation=False`?
- How is the LLM configured?

---

#### File: `agents/jd_parser/tools.py`

**Purpose**: Define tools that JD Parser agent can use.

**What to Look For**:
- Tool function signatures
- Input/output types
- Error handling
- Integration with shared services

**Key Code Patterns**:
```python
from crewai_tools import tool
from shared.bedrock_client import BedrockClient
from shared.models import JobDescription
from typing import Dict
import json

@tool
def extract_requirements(jd_text: str) -> Dict:
    """Extract structured requirements from job description text
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        Dictionary with title, skills, experience, etc.
    """
    
    bedrock = BedrockClient()
    
    prompt = f"""
    Extract the following from this job description:
    - Job title
    - Required skills (list)
    - Years of experience required
    - Education requirements
    - Key responsibilities (top 3)
    
    Job Description:
    {jd_text}
    
    Output as JSON:
    {{
        "title": "...",
        "required_skills": [...],
        "experience_years": X,
        "education": "...",
        "responsibilities": [...]
    }}
    """
    
    response = bedrock.invoke(prompt, temperature=0.3)  # Low temp for extraction
    
    try:
        requirements = json.loads(response)
        return requirements
    except json.JSONDecodeError:
        return {"error": "Failed to parse response"}

@tool
def parse_skills(skills_text: str) -> list:
    """Parse and normalize skill names
    
    Args:
        skills_text: Comma or newline separated skills
        
    Returns:
        List of normalized skill names
    """
    # Split by comma or newline
    skills = [s.strip() for s in skills_text.replace('\n', ',').split(',')]
    
    # Normalize (lowercase, remove duplicates)
    normalized = list(set(s.lower() for s in skills if s))
    
    return normalized
```

**Questions to Answer**:
- What does each tool do?
- How do tools use shared services?
- Why low temperature for extraction?
- How are errors handled?

---

#### File: `agents/jd_parser/prompts.py`

**Purpose**: Store prompt templates for JD Parser agent.

**What to Look For**:
- Prompt structure and formatting
- Few-shot examples
- Output format specifications
- Variable placeholders

**Key Code Patterns**:
```python
JD_EXTRACTION_PROMPT = """
You are analyzing a job description to extract structured information.

Job Description:
{jd_text}

Extract the following information:

1. Job Title: The exact title of the position
2. Required Skills: Technical and soft skills (as list)
3. Experience: Years of experience required (number)
4. Education: Degree requirements
5. Responsibilities: Top 3-5 key responsibilities

Output Format (JSON):
{{
    "title": "Senior Python Developer",
    "required_skills": ["Python", "AWS", "Docker", "CI/CD"],
    "experience_years": 5,
    "education": "Bachelor's in Computer Science or equivalent",
    "responsibilities": [
        "Design and implement microservices",
        "Lead technical architecture decisions",
        "Mentor junior developers"
    ]
}}

Be precise and extract only what's explicitly stated.
"""

SKILL_NORMALIZATION_PROMPT = """
Normalize these skills to standard industry terms:

Input Skills:
{skills}

Rules:
- Use standard capitalization (e.g., "Python" not "python")
- Expand abbreviations (e.g., "JavaScript" not "JS")
- Remove duplicates
- Group related skills (e.g., "React", "React.js" → "React")

Output as JSON array: ["Skill 1", "Skill 2", ...]
"""
```

**Questions to Answer**:
- Why separate prompts from code?
- How are variables injected?
- Why specify output format?
- What makes a good prompt?

---

#### File: `agents/jd_parser/lambda_handler.py`

**Purpose**: Lambda entry point that wraps agent execution.

**What to Look For**:
- Event parsing
- Agent invocation
- Response formatting
- Error handling
- Logging

**Key Code Patterns**:
```python
import json
from .agent import create_jd_parser_agent
from crewai import Task, Crew
from shared.logger import get_logger
from shared.dynamodb_client import DynamoDBClient
from shared.models import JobDescription

logger = get_logger(__name__)
db_client = DynamoDBClient('job_descriptions')

def lambda_handler(event, context):
    """Lambda handler for JD Parser agent"""
    
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        jd_text = body.get('job_description')
        job_id = body.get('job_id')
        
        if not jd_text or not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing job_description or job_id'})
            }
        
        logger.info(f"Processing job_id: {job_id}")
        
        # Create agent and task
        agent = create_jd_parser_agent()
        
        task = Task(
            description=f"Parse this job description and extract requirements:\n\n{jd_text}",
            agent=agent,
            expected_output='Structured job requirements as JSON'
        )
        
        # Execute
        crew = Crew(agents=[agent], tasks=[task])
        result = crew.kickoff()
        
        # Parse result
        requirements = json.loads(str(result))
        
        # Create JobDescription model
        job_desc = JobDescription(
            job_id=job_id,
            **requirements
        )
        
        # Save to DynamoDB
        db_client.put_item(job_desc.to_dynamodb())
        
        logger.info(f"Successfully parsed job_id: {job_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'job_id': job_id,
                'requirements': requirements
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

**Questions to Answer**:
- How is input validated?
- How is the agent invoked?
- Where is output stored?
- How are errors handled?
- What's logged?

---

### 6.4 Orchestration Layer

#### File: `agents/supervisor/agent.py`

**Purpose**: Supervisor agent that orchestrates the entire workflow.

**What to Look For**:
- Hierarchical process setup
- Agent delegation logic
- Workflow state management
- Error recovery

**Key Code Patterns**:
```python
from crewai import Agent, Task, Crew, Process
from typing import List, Dict

def create_supervisor_agent() -> Agent:
    """Create supervisor agent with delegation capability"""
    
    agent = Agent(
        role='Talent Acquisition Supervisor',
        goal='Orchestrate end-to-end candidate screening workflow',
        backstory="""You are an experienced hiring manager who coordinates 
        a team of specialists to efficiently screen candidates. You delegate 
        tasks to the right specialists and ensure quality outcomes.""",
        tools=[],  # Supervisor doesn't use tools directly
        allow_delegation=True,  # Can delegate to other agents
        verbose=True
    )
    
    return agent

def create_workflow_crew(
    jd_text: str,
    candidate_resumes: List[str]
) -> Crew:
    """Create crew with supervisor and all agents"""
    
    # Create all agents
    supervisor = create_supervisor_agent()
    jd_parser = create_jd_parser_agent()
    sourcer = create_candidate_sourcer_agent()
    screener = create_resume_screener_agent()
    interviewer = create_interview_agent()
    reporter = create_report_generator_agent()
    
    # Define workflow tasks
    tasks = [
        Task(
            description=f"Parse job requirements from: {jd_text}",
            agent=jd_parser,
            expected_output='Structured requirements'
        ),
        Task(
            description="Source additional candidates if needed",
            agent=sourcer,
            expected_output='List of candidate profiles'
        ),
        Task(
            description=f"Screen these {len(candidate_resumes)} resumes against requirements",
            agent=screener,
            expected_output='Ranked list of candidates with scores'
        ),
        Task(
            description="Generate interview questions for top 3 candidates",
            agent=interviewer,
            expected_output='Interview questions per candidate'
        ),
        Task(
            description="Generate final hiring recommendation report",
            agent=reporter,
            expected_output='Comprehensive report with recommendations'
        )
    ]
    
    # Create crew with hierarchical process
    crew = Crew(
        agents=[supervisor, jd_parser, sourcer, screener, interviewer, reporter],
        tasks=tasks,
        process=Process.hierarchical,  # Supervisor manages workflow
        manager_agent=supervisor,
        verbose=True
    )
    
    return crew
```

**Questions to Answer**:
- How does supervisor delegate tasks?
- What's the task execution order?
- How is state passed between tasks?
- What happens if a task fails?

---


## 7. Integration Flows & Data Paths

### 7.1 End-to-End Workflow

**Scenario**: Screen 10 candidates for a Senior Python Developer role

**Flow**:

```
1. API Request
   ↓
   POST /api/screen-candidates
   Body: {
     "job_description": "...",
     "candidate_resumes": ["resume1.pdf", ...]
   }

2. API Gateway → Supervisor Lambda
   ↓
   Event: {
     "body": "{...}",
     "headers": {...}
   }

3. Supervisor Agent Initialization
   ↓
   - Parse request
   - Create workflow crew
   - Initialize all agents

4. Task 1: JD Parser
   ↓
   Input: job_description text
   Process: Extract requirements via Bedrock
   Output: {title, required_skills, experience_years}
   Storage: DynamoDB job_descriptions table

5. Task 2: Candidate Sourcer (Optional)
   ↓
   Input: requirements from Task 1
   Process: Search external sources if needed
   Output: Additional candidate profiles
   Storage: DynamoDB candidates table

6. Task 3: Resume Screener
   ↓
   Input: requirements + candidate_resumes
   Process: Score each resume via Bedrock
   Output: Ranked candidates with scores
   Storage: DynamoDB screening_results table

7. Task 4: Interview Agent
   ↓
   Input: Top 3 candidates from Task 3
   Process: Generate tailored questions via Bedrock
   Output: Interview questions per candidate
   Storage: DynamoDB interview_questions table

8. Task 5: Report Generator
   ↓
   Input: All previous task outputs
   Process: Synthesize comprehensive report via Bedrock
   Output: Hiring recommendation report
   Storage: DynamoDB reports table

9. Supervisor Returns Response
   ↓
   Response: {
     "statusCode": 200,
     "body": {
       "report_id": "...",
       "top_candidates": [...],
       "report_url": "..."
     }
   }

10. API Gateway → Client
    ↓
    HTTP 200 with JSON response
```

---

### 7.2 Data Flow Between Agents

**State Management Pattern**:

```python
# Workflow state stored in DynamoDB
workflow_state = {
    'workflow_id': 'wf_12345',
    'status': 'in_progress',
    'current_task': 'screening',
    'completed_tasks': ['jd_parsing'],
    'task_outputs': {
        'jd_parsing': {
            'job_id': 'job_001',
            'requirements': {...}
        }
    },
    'created_at': '2026-03-15T10:00:00Z',
    'updated_at': '2026-03-15T10:05:00Z'
}
```

**Agent Communication**:

```
Agent A completes task
    ↓
Writes output to DynamoDB
    ↓
Updates workflow_state
    ↓
Supervisor reads workflow_state
    ↓
Passes relevant data to Agent B
    ↓
Agent B executes with context
```

**No Direct Agent-to-Agent Communication**: All communication goes through DynamoDB and supervisor.

---

### 7.3 Error Handling Flow

**Scenario**: Bedrock API call fails in Resume Screener

```
1. Resume Screener calls Bedrock
   ↓
2. Bedrock returns 429 (Throttling)
   ↓
3. BedrockClient catches ClientError
   ↓
4. Retry with exponential backoff (3 attempts)
   ↓
5. If all retries fail:
   ↓
6. Log error to CloudWatch
   ↓
7. Update workflow_state: status = 'failed'
   ↓
8. Return error to Supervisor
   ↓
9. Supervisor logs failure
   ↓
10. Return 500 response to client with error details
```

**Retry Strategy**:
- Attempt 1: Immediate
- Attempt 2: Wait 2s
- Attempt 3: Wait 4s
- After 3 failures: Propagate error

---

### 7.4 Tracing a Request

**How to trace a specific request through the system**:

1. **Find Request ID**:
```bash
# In CloudWatch Logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/supervisor \
  --filter-pattern "workflow_id: wf_12345"
```

2. **Check Workflow State**:
```python
# Query DynamoDB
db_client = DynamoDBClient('workflow_state')
state = db_client.get_item({'workflow_id': 'wf_12345'})
print(state['completed_tasks'])
print(state['current_task'])
```

3. **Check Task Outputs**:
```python
# Get JD parsing output
jd_output = state['task_outputs']['jd_parsing']

# Get screening results
screening_client = DynamoDBClient('screening_results')
results = screening_client.query(
    'workflow_id = :wf_id',
    {':wf_id': 'wf_12345'}
)
```

4. **Check Agent Logs**:
```bash
# JD Parser logs
aws logs tail /aws/lambda/jd-parser --follow

# Screener logs
aws logs tail /aws/lambda/resume-screener --follow
```

---

## 8. Verification Checkpoints

### Checkpoint 1: Infrastructure Understanding

**Complete after reading infrastructure layer**

**Questions**:

1. What are the primary keys for each DynamoDB table?
   - job_descriptions: `job_id` (partition key)
   - candidates: `candidate_id` (partition key)
   - screening_results: `workflow_id` (partition key), `candidate_id` (sort key)
   - workflow_state: `workflow_id` (partition key)

2. What permissions does the Resume Screener Lambda need?
   - DynamoDB: GetItem, PutItem, Query on screening_results and candidates tables
   - Bedrock: InvokeModel on amazon.nova-lite-v1:0
   - CloudWatch: CreateLogGroup, CreateLogStream, PutLogEvents

3. How does a client trigger the workflow?
   - POST request to API Gateway endpoint `/api/screen-candidates`
   - API Gateway invokes Supervisor Lambda
   - Supervisor orchestrates agent workflow

**Hands-On Task**:
- Create a DynamoDB table locally using boto3
- Define an IAM policy for one agent
- Write a simple Lambda handler that returns "Hello"

**Pass Criteria**: Can explain infrastructure components and their interactions.

---

### Checkpoint 2: Shared Services Understanding

**Complete after reading shared services layer**

**Questions**:

1. Why use Pydantic models?
   - Type validation at runtime
   - Automatic serialization/deserialization
   - Clear data contracts between components
   - IDE autocomplete support

2. How does DynamoDBClient handle throttling?
   - Catches `ProvisionedThroughputExceededException`
   - Retries with exponential backoff (2^attempt seconds)
   - Maximum 3 retry attempts
   - Logs warnings on throttle

3. Why track token usage in BedrockClient?
   - Monitor costs (tokens = money)
   - Optimize prompt length
   - Debug performance issues
   - Capacity planning

**Hands-On Task**:
- Create a Pydantic model for a new entity
- Write a function that uses DynamoDBClient to save/retrieve data
- Make a Bedrock API call and log token usage

**Pass Criteria**: Can use shared services independently.

---

### Checkpoint 3: Agent Understanding

**Complete after reading one agent (e.g., JD Parser)**

**Questions**:

1. What is the JD Parser agent's role?
   - Extract structured requirements from job description text
   - Normalize skill names
   - Identify experience requirements
   - Parse responsibilities

2. What tools does it use?
   - `extract_requirements`: Bedrock-powered extraction
   - `parse_skills`: Skill normalization
   - Both tools use BedrockClient

3. How does the Lambda handler invoke the agent?
   - Creates agent instance
   - Defines Task with description
   - Creates Crew with agent and task
   - Calls `crew.kickoff()`
   - Parses result and saves to DynamoDB

**Hands-On Task**:
- Create a simple agent with one tool
- Write a Lambda handler that invokes the agent
- Test locally with mock event

**Pass Criteria**: Can create and invoke a basic agent.

---

### Checkpoint 4: Integration Understanding

**Complete after reading supervisor and integration tests**

**Questions**:

1. How does the supervisor delegate tasks?
   - Uses hierarchical process in CrewAI
   - Defines tasks with specific agents
   - CrewAI handles delegation automatically
   - Supervisor monitors progress

2. How is state passed between agents?
   - Each agent writes output to DynamoDB
   - Supervisor reads from DynamoDB
   - Passes relevant data to next agent via task description
   - No direct agent-to-agent communication

3. What happens if an agent fails?
   - Agent logs error
   - Updates workflow_state to 'failed'
   - Returns error to supervisor
   - Supervisor propagates error to client
   - No automatic retry (manual intervention required)

**Hands-On Task**:
- Trace a request through CloudWatch logs
- Query workflow_state for a specific workflow
- Simulate an agent failure and observe error handling

**Pass Criteria**: Can trace and debug end-to-end workflows.

---


## 9. Reference Library

### 9.1 API Quick Reference

#### DynamoDB Operations

```python
# Initialize client
from shared.dynamodb_client import DynamoDBClient
db = DynamoDBClient('table_name')

# Put item
db.put_item({'id': '123', 'name': 'John'})

# Get item
item = db.get_item({'id': '123'})

# Query (requires partition key)
items = db.query(
    'id = :id',
    {':id': '123'}
)

# Update item
db.update_item(
    {'id': '123'},
    'SET #name = :name',
    {'#name': 'name'},
    {':name': 'Jane'}
)

# Delete item
db.delete_item({'id': '123'})
```

#### Bedrock Operations

```python
# Initialize client
from shared.bedrock_client import BedrockClient
bedrock = BedrockClient()

# Simple invocation
response = bedrock.invoke(
    prompt="Extract skills from: ...",
    max_tokens=500,
    temperature=0.7
)

# With template
response = bedrock.invoke_with_template(
    template="Extract {field} from: {text}",
    variables={'field': 'skills', 'text': '...'},
    temperature=0.3
)
```

#### CrewAI Agent Creation

```python
from crewai import Agent, Task, Crew

# Create agent
agent = Agent(
    role='Role Name',
    goal='What agent should achieve',
    backstory='Agent background and expertise',
    tools=[tool1, tool2],
    llm=bedrock_client,
    verbose=True,
    allow_delegation=False
)

# Create task
task = Task(
    description='Detailed task description',
    agent=agent,
    expected_output='What output should look like'
)

# Create crew
crew = Crew(
    agents=[agent],
    tasks=[task],
    verbose=True
)

# Execute
result = crew.kickoff()
```

#### Lambda Handler Pattern

```python
import json
from shared.logger import get_logger

logger = get_logger(__name__)

def lambda_handler(event, context):
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        
        # Validate
        if not body.get('required_field'):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required_field'})
            }
        
        # Process
        result = process_data(body)
        
        # Return success
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

---

### 9.2 Common Patterns

#### Pattern 1: Retry with Exponential Backoff

```python
import time
from botocore.exceptions import ClientError

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            time.sleep(wait_time)
```

#### Pattern 2: Structured Logging

```python
from shared.logger import get_logger

logger = get_logger(__name__)

def process_item(item_id):
    logger.info(f"Processing item", extra={
        'item_id': item_id,
        'action': 'process'
    })
    
    try:
        # Process
        result = do_work(item_id)
        logger.info(f"Completed", extra={
            'item_id': item_id,
            'result': result
        })
        return result
    except Exception as e:
        logger.error(f"Failed", extra={
            'item_id': item_id,
            'error': str(e)
        })
        raise
```

#### Pattern 3: Pydantic Model Validation

```python
from pydantic import BaseModel, Field, validator
from typing import List

class Candidate(BaseModel):
    candidate_id: str
    name: str
    skills: List[str]
    experience_years: int = Field(ge=0, le=50)
    
    @validator('skills')
    def skills_not_empty(cls, v):
        if not v:
            raise ValueError('Skills cannot be empty')
        return v
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

# Usage
try:
    candidate = Candidate(
        candidate_id='c1',
        name='John Doe',
        skills=['Python'],
        experience_years=5
    )
except ValidationError as e:
    print(e.json())
```

#### Pattern 4: DynamoDB Pagination

```python
def get_all_items(table_name, key_condition, expression_values):
    """Get all items with pagination"""
    db = DynamoDBClient(table_name)
    all_items = []
    last_key = None
    
    while True:
        params = {
            'KeyConditionExpression': key_condition,
            'ExpressionAttributeValues': expression_values
        }
        
        if last_key:
            params['ExclusiveStartKey'] = last_key
        
        response = db.table.query(**params)
        all_items.extend(response.get('Items', []))
        
        last_key = response.get('LastEvaluatedKey')
        if not last_key:
            break
    
    return all_items
```

#### Pattern 5: Prompt Template Management

```python
# prompts.py
EXTRACTION_PROMPT = """
Task: {task_description}

Input:
{input_text}

Output Format:
{output_format}

Example:
{example}

Output:
"""

# Usage
from .prompts import EXTRACTION_PROMPT

prompt = EXTRACTION_PROMPT.format(
    task_description="Extract candidate skills",
    input_text=resume_text,
    output_format="JSON array",
    example='["Python", "AWS"]'
)

response = bedrock.invoke(prompt)
```

---

### 9.3 Configuration Reference

#### Environment Variables

```bash
# Lambda environment variables
AWS_REGION=us-east-1
DYNAMODB_TABLE_PREFIX=talent-acq-
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=300
```

#### DynamoDB Table Names

```
job_descriptions
candidates
screening_results
interview_questions
reports
workflow_state
```

#### IAM Policy Template

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/TABLE_NAME"
    },
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:*:*:model/amazon.nova-lite-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

### 9.4 Debugging Commands

#### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/supervisor --follow

# Filter logs by pattern
aws logs filter-log-events \
  --log-group-name /aws/lambda/supervisor \
  --filter-pattern "ERROR"

# Get logs for specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/supervisor \
  --start-time $(date -d '1 hour ago' +%s)000
```

#### DynamoDB Queries

```bash
# Get item
aws dynamodb get-item \
  --table-name workflow_state \
  --key '{"workflow_id": {"S": "wf_12345"}}'

# Query items
aws dynamodb query \
  --table-name screening_results \
  --key-condition-expression "workflow_id = :wf_id" \
  --expression-attribute-values '{":wf_id": {"S": "wf_12345"}}'

# Scan table (expensive!)
aws dynamodb scan \
  --table-name candidates \
  --filter-expression "experience_years > :exp" \
  --expression-attribute-values '{":exp": {"N": "5"}}'
```

#### Lambda Invocation

```bash
# Invoke Lambda directly
aws lambda invoke \
  --function-name jd-parser \
  --payload '{"body": "{\"job_description\": \"...\"}"}' \
  response.json

# Check function configuration
aws lambda get-function-configuration \
  --function-name jd-parser
```

---

## 10. Troubleshooting Guide

### Issue 1: Lambda Timeout

**Symptoms**:
- Lambda execution exceeds timeout (default 3s, max 15min)
- Partial results in DynamoDB
- CloudWatch shows "Task timed out after X seconds"

**Causes**:
- Bedrock API slow response
- Large batch processing
- Cold start overhead
- Inefficient code

**Solutions**:
1. Increase Lambda timeout:
```python
# In infrastructure code
lambda_function.timeout = Duration.minutes(5)
```

2. Optimize Bedrock calls:
```python
# Reduce max_tokens
bedrock.invoke(prompt, max_tokens=200)  # Instead of 1000

# Use async for parallel calls
results = await asyncio.gather(
    bedrock.invoke(prompt1),
    bedrock.invoke(prompt2)
)
```

3. Process in batches:
```python
# Instead of processing 100 resumes at once
for batch in chunks(resumes, 10):
    process_batch(batch)
```

---

### Issue 2: DynamoDB Throttling

**Symptoms**:
- `ProvisionedThroughputExceededException`
- Slow response times
- Failed writes

**Causes**:
- Exceeded read/write capacity units
- Hot partition key
- Burst traffic

**Solutions**:
1. Switch to on-demand mode:
```python
# In table definition
BillingMode='PAY_PER_REQUEST'
```

2. Implement exponential backoff (already in DynamoDBClient)

3. Use batch operations:
```python
# Instead of multiple put_item calls
with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)
```

4. Distribute partition keys:
```python
# Add random suffix to partition key
partition_key = f"{workflow_id}#{random.randint(0, 9)}"
```

---

### Issue 3: Bedrock API Errors

**Symptoms**:
- 429 Throttling errors
- 400 Validation errors
- 500 Internal errors

**Causes**:
- Rate limit exceeded
- Invalid prompt format
- Model unavailable
- Token limit exceeded

**Solutions**:
1. Handle throttling:
```python
# Already implemented in BedrockClient
# Retry with exponential backoff
```

2. Validate prompt length:
```python
def validate_prompt(prompt: str, max_tokens: int = 300000):
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = len(prompt) / 4
    if estimated_tokens > max_tokens:
        raise ValueError(f"Prompt too long: {estimated_tokens} tokens")
```

3. Use appropriate temperature:
```python
# For extraction/classification: low temperature
bedrock.invoke(prompt, temperature=0.3)

# For creative generation: higher temperature
bedrock.invoke(prompt, temperature=0.7)
```

---

### Issue 4: Agent Not Producing Expected Output

**Symptoms**:
- Agent returns empty response
- Output format incorrect
- Agent ignores instructions

**Causes**:
- Unclear prompt
- Missing examples
- Wrong temperature
- Tool not working

**Solutions**:
1. Improve prompt clarity:
```python
# Bad prompt
"Extract skills"

# Good prompt
"""
Extract technical skills from the resume below.

Resume:
{resume_text}

Output as JSON array: ["Skill 1", "Skill 2"]

Example: ["Python", "AWS", "Docker"]

Skills:
"""
```

2. Add few-shot examples:
```python
prompt = f"""
Task: Extract skills

Example 1:
Input: "5 years Python, AWS certified"
Output: ["Python", "AWS"]

Example 2:
Input: "React developer, TypeScript expert"
Output: ["React", "TypeScript"]

Now extract from:
{resume_text}

Output:
"""
```

3. Test tools independently:
```python
# Test tool outside agent
from agents.jd_parser.tools import extract_requirements

result = extract_requirements("Job description text...")
print(result)
```

---

### Issue 5: Workflow State Inconsistency

**Symptoms**:
- Workflow stuck in "in_progress"
- Missing task outputs
- Duplicate processing

**Causes**:
- Agent failure without state update
- Race condition in concurrent updates
- Incomplete error handling

**Solutions**:
1. Use atomic updates:
```python
# Use UpdateItem with conditions
db.table.update_item(
    Key={'workflow_id': wf_id},
    UpdateExpression='SET #status = :status',
    ConditionExpression='#status = :old_status',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':status': 'completed',
        ':old_status': 'in_progress'
    }
)
```

2. Implement state machine:
```python
VALID_TRANSITIONS = {
    'pending': ['in_progress', 'failed'],
    'in_progress': ['completed', 'failed'],
    'completed': [],
    'failed': ['pending']  # Allow retry
}

def update_status(current, new):
    if new not in VALID_TRANSITIONS[current]:
        raise ValueError(f"Invalid transition: {current} -> {new}")
```

3. Add cleanup Lambda:
```python
# Scheduled Lambda to clean up stuck workflows
def cleanup_handler(event, context):
    # Find workflows in_progress > 1 hour
    stuck = find_stuck_workflows()
    for wf in stuck:
        update_status(wf['workflow_id'], 'failed')
```

---

### Issue 6: High Costs

**Symptoms**:
- AWS bill higher than expected
- Many Bedrock API calls
- High DynamoDB costs

**Causes**:
- Inefficient prompts (too many tokens)
- Unnecessary API calls
- DynamoDB scans instead of queries
- No caching

**Solutions**:
1. Optimize prompts:
```python
# Bad: Include entire resume in prompt
prompt = f"Extract skills from: {full_resume_text}"

# Good: Extract relevant section first
relevant_section = extract_skills_section(resume_text)
prompt = f"Extract skills from: {relevant_section}"
```

2. Cache results:
```python
# Check cache before Bedrock call
cache_key = hashlib.md5(prompt.encode()).hexdigest()
cached = db.get_item({'cache_key': cache_key})

if cached:
    return cached['result']
else:
    result = bedrock.invoke(prompt)
    db.put_item({'cache_key': cache_key, 'result': result})
    return result
```

3. Use queries instead of scans:
```python
# Bad: Scan entire table
response = table.scan(
    FilterExpression='experience_years > :exp',
    ExpressionAttributeValues={':exp': 5}
)

# Good: Query with GSI
response = table.query(
    IndexName='experience_index',
    KeyConditionExpression='experience_years > :exp',
    ExpressionAttributeValues={':exp': 5}
)
```

---

## Learning Path Summary

### Week 1: Foundation
- **Days 1-2**: Complete technology deep-dives, do Labs 1-3
- **Day 3**: Complete Labs 4-5, understand CrewAI basics

### Week 2: Codebase Deep-Dive
- **Days 4-5**: Read infrastructure and shared services layers
- **Days 6-7**: Read agent layer (all 5 agents)
- **Day 8**: Read supervisor and orchestration

### Week 3: Mastery
- **Days 9-10**: Trace integration flows, complete all checkpoints
- **Days 11-12**: Modify code, add features, debug issues
- **Days 13-14**: Build new agent or extend existing functionality

---

## Next Steps

After completing this learning system:

1. **Build a new agent**: Create a "Salary Negotiator" agent
2. **Optimize performance**: Reduce Bedrock token usage by 30%
3. **Add monitoring**: Implement CloudWatch dashboards
4. **Write tests**: Achieve 80% code coverage
5. **Deploy to production**: Set up CI/CD pipeline

---

## Additional Resources

### Official Documentation
- AWS Lambda: https://docs.aws.amazon.com/lambda/
- DynamoDB: https://docs.aws.amazon.com/dynamodb/
- Bedrock: https://docs.aws.amazon.com/bedrock/
- CrewAI: https://docs.crewai.com/
- Python Asyncio: https://docs.python.org/3/library/asyncio.html

### Tutorials
- AWS Serverless Workshop: https://aws.amazon.com/serverless/workshops/
- DynamoDB Best Practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html
- Prompt Engineering Guide: https://www.promptingguide.ai/

### Community
- AWS re:Post: https://repost.aws/
- CrewAI Discord: https://discord.gg/crewai
- Stack Overflow: Tag questions with `aws-lambda`, `dynamodb`, `amazon-bedrock`

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-15  
**Maintained By**: Development Team  
**Feedback**: Open an issue or submit a PR
