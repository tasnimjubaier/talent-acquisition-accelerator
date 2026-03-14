"""
Data Models for Talent Acquisition Accelerator

Pydantic models for type-safe data structures used across all agents.
These models ensure data validation and provide clear schemas for DynamoDB items.

References:
- 10_data_architecture.md: Database schema and data flow
- 16_module_build_checklist.md: Phase 2 implementation requirements

Verification Sources:
- Pydantic Documentation: https://docs.pydantic.dev/latest/
- DynamoDB Data Modeling: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import uuid


# ============================================================================
# Enums for Status Values
# ============================================================================

class JobStatus(str, Enum):
    """Job posting status"""
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    FILLED = "filled"
    CANCELLED = "cancelled"


class CandidateStatus(str, Enum):
    """Candidate pipeline status"""
    SOURCED = "sourced"
    SCREENING = "screening"
    SCREENED = "screened"
    OUTREACH_PENDING = "outreach_pending"
    OUTREACH_SENT = "outreach_sent"
    RESPONDED = "responded"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    EVALUATING = "evaluating"
    OFFER_PENDING = "offer_pending"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class InteractionType(str, Enum):
    """Type of candidate interaction"""
    SOURCED = "sourced"
    SCREENED = "screened"
    OUTREACH_SENT = "outreach_sent"
    RESPONSE_RECEIVED = "response_received"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    EVALUATION_COMPLETED = "evaluation_completed"
    NOTE_ADDED = "note_added"


# ============================================================================
# Core Data Models
# ============================================================================

class Job(BaseModel):
    """
    Job posting model
    
    Represents a job opening in the recruiting pipeline.
    Maps to DynamoDB 'talent-acq-jobs' table.
    """
    job_id: str = Field(default_factory=lambda: f"job-{uuid.uuid4()}")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Job details
    department: Optional[str] = None
    location: Optional[str] = None
    remote_allowed: bool = False
    salary_range: Optional[Dict[str, float]] = None  # {"min": 80000, "max": 120000}
    
    # Status tracking
    status: JobStatus = JobStatus.DRAFT
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    closed_at: Optional[int] = None
    
    # Metrics
    candidates_sourced: int = 0
    candidates_screened: int = 0
    interviews_scheduled: int = 0
    offers_made: int = 0
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'jobId': self.job_id,
            'title': self.title,
            'description': self.description,
            'requirements': self.requirements,
            'department': self.department,
            'location': self.location,
            'remoteAllowed': self.remote_allowed,
            'salaryRange': self.salary_range,
            'status': self.status,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at,
            'closedAt': self.closed_at,
            'candidatesSourced': self.candidates_sourced,
            'candidatesScreened': self.candidates_screened,
            'interviewsScheduled': self.interviews_scheduled,
            'offersMade': self.offers_made
        }


class Candidate(BaseModel):
    """
    Candidate model
    
    Represents a candidate in the recruiting pipeline.
    Maps to DynamoDB 'talent-acq-candidates' table.
    """
    candidate_id: str = Field(default_factory=lambda: f"cand-{uuid.uuid4()}")
    job_id: str = Field(..., min_length=1)
    
    # Personal information
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    
    # Professional information
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_experience: Optional[int] = None
    skills: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    
    # Profile links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    
    # Pipeline tracking
    status: CandidateStatus = CandidateStatus.SOURCED
    source: Optional[str] = None  # "linkedin", "github", "referral", etc.
    
    # Scoring
    fit_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    screening_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    interview_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    overall_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Timestamps
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    last_contacted_at: Optional[int] = None
    
    # Agent outputs
    sourcing_notes: Optional[str] = None
    screening_notes: Optional[str] = None
    outreach_message: Optional[str] = None
    evaluation_summary: Optional[str] = None
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'candidateId': self.candidate_id,
            'jobId': self.job_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'currentTitle': self.current_title,
            'currentCompany': self.current_company,
            'yearsExperience': self.years_experience,
            'skills': self.skills,
            'education': self.education,
            'linkedinUrl': self.linkedin_url,
            'githubUrl': self.github_url,
            'portfolioUrl': self.portfolio_url,
            'resumeUrl': self.resume_url,
            'status': self.status,
            'source': self.source,
            'fitScore': self.fit_score,
            'screeningScore': self.screening_score,
            'interviewScore': self.interview_score,
            'overallScore': self.overall_score,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at,
            'lastContactedAt': self.last_contacted_at,
            'sourcingNotes': self.sourcing_notes,
            'screeningNotes': self.screening_notes,
            'outreachMessage': self.outreach_message,
            'evaluationSummary': self.evaluation_summary
        }



class Interaction(BaseModel):
    """
    Interaction model
    
    Represents an interaction with a candidate (outreach, screening, interview, etc.)
    Maps to DynamoDB 'talent-acq-interactions' table.
    """
    interaction_id: str = Field(default_factory=lambda: f"int-{uuid.uuid4()}")
    candidate_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    
    # Interaction details
    interaction_type: InteractionType
    agent_name: str = Field(..., min_length=1)  # Which agent created this interaction
    
    # Content
    subject: Optional[str] = None
    message: Optional[str] = None
    response: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    response_timestamp: Optional[int] = None
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'interactionId': self.interaction_id,
            'candidateId': self.candidate_id,
            'jobId': self.job_id,
            'interactionType': self.interaction_type,
            'agentName': self.agent_name,
            'subject': self.subject,
            'message': self.message,
            'response': self.response,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'responseTimestamp': self.response_timestamp
        }


class AgentState(BaseModel):
    """
    Agent state model
    
    Tracks the state and execution history of agent workflows.
    Maps to DynamoDB 'talent-acq-agent-state' table.
    """
    state_id: str = Field(default_factory=lambda: f"state-{uuid.uuid4()}")
    job_id: str = Field(..., min_length=1)
    
    # Workflow tracking
    current_agent: Optional[str] = None
    workflow_status: str = "initialized"  # initialized, in_progress, completed, failed
    
    # Agent execution history
    agents_executed: List[str] = Field(default_factory=list)
    current_step: int = 0
    total_steps: int = 5  # 5 agents in pipeline
    
    # Shared context between agents
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Results from each agent
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Cost tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    
    # Timestamps
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    completed_at: Optional[int] = None
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'stateId': self.state_id,
            'jobId': self.job_id,
            'currentAgent': self.current_agent,
            'workflowStatus': self.workflow_status,
            'agentsExecuted': self.agents_executed,
            'currentStep': self.current_step,
            'totalSteps': self.total_steps,
            'sharedContext': self.shared_context,
            'agentResults': self.agent_results,
            'errors': self.errors,
            'totalInputTokens': self.total_input_tokens,
            'totalOutputTokens': self.total_output_tokens,
            'totalCostUsd': self.total_cost_usd,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at,
            'completedAt': self.completed_at
        }


# ============================================================================
# Helper Functions
# ============================================================================

def from_dynamodb_item(item: dict, model_class):
    """
    Convert DynamoDB item to Pydantic model
    
    Args:
        item: DynamoDB item (dict)
        model_class: Pydantic model class to convert to
        
    Returns:
        Instance of model_class
    """
    # Convert camelCase keys to snake_case
    snake_case_item = {}
    for key, value in item.items():
        # Simple camelCase to snake_case conversion
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        snake_case_item[snake_key] = value
    
    return model_class(**snake_case_item)
