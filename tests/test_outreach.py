"""
Unit Tests for Outreach Agent

Tests the Outreach Agent's ability to generate personalized outreach messages,
handle multiple channels and tones, calculate personalization scores, and
integrate with DynamoDB.

Run with: pytest tests/test_outreach.py -v
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import agent and dependencies
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.outreach_agent import OutreachAgent
from shared.models import Candidate, Interaction, InteractionType, CandidateStatus
from shared.config import Config


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def outreach_agent():
    """Create OutreachAgent instance for testing"""
    return OutreachAgent()


@pytest.fixture
def sample_job_details():
    """Sample job details for testing"""
    return {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "description": "Build scalable cloud systems using Python and AWS. Work with a talented team on cutting-edge projects.",
        "location": "Seattle, WA",
        "remote_allowed": True,
        "requirements": {
            "required_skills": ["Python", "AWS", "React"],
            "preferred_skills": ["Docker", "Kubernetes"],
            "experience_years": {"min": 5, "max": 10}
        },
        "salary_range": {"min": 140000, "max": 180000}
    }


@pytest.fixture
def sample_candidate():
    """Sample candidate for testing"""
    return {
        "candidate_id": "cand-001",
        "name": "Alice Johnson",
        "current_title": "Software Engineer",
        "current_company": "CloudTech Inc",
        "location": "Seattle, WA",
        "strengths": [
            "Python expert with 7 years experience",
            "AWS certified solutions architect",
            "Strong React and frontend skills"
        ],
        "screening_score": 0.92,
        "skills": ["Python", "AWS", "React", "Docker"]
    }


@pytest.fixture
def sample_candidates(sample_candidate):
    """List of sample candidates"""
    return [
        sample_candidate,
        {
            "candidate_id": "cand-002",
            "name": "Bob Smith",
            "current_title": "Backend Developer",
            "current_company": "DataCorp",
            "location": "Remote",
            "strengths": [
                "Python backend specialist",
                "AWS infrastructure expert"
            ],
            "screening_score": 0.85,
            "skills": ["Python", "AWS", "PostgreSQL"]
        }
    ]


@pytest.fixture
def mock_nova_response_email():
    """Mock Nova response for email generation"""
    return {
        'success': True,
        'content': json.dumps({
            "subject": "Exciting Senior Engineer Opportunity at TechCorp",
            "message": "Hi Alice,\n\nI came across your profile and was impressed by your Python expertise and AWS certification. Your 7 years of experience building scalable systems aligns perfectly with what we're looking for at TechCorp.\n\nWe're hiring a Senior Software Engineer to work on cutting-edge cloud infrastructure. Given your background at CloudTech Inc and your strong React skills, I think you'd be a great fit.\n\nWould you be open to a brief call this week to discuss the opportunity?\n\nBest regards,\n[Recruiter Name]",
            "call_to_action": "Schedule a 15-minute call this week"
        }),
        'input_tokens': 450,
        'output_tokens': 180,
        'cost_usd': 0.00006,
        'latency': 2.3
    }


@pytest.fixture
def mock_nova_response_linkedin():
    """Mock Nova response for LinkedIn InMail"""
    return {
        'success': True,
        'content': json.dumps({
            "message": "Hi Alice,\n\nYour Python and AWS expertise caught my attention. We're building something exciting at TechCorp and your background at CloudTech Inc would be a perfect fit.\n\nInterested in learning more about our Senior Engineer role?\n\nBest,\n[Recruiter]",
            "call_to_action": "Reply if interested"
        }),
        'input_tokens': 380,
        'output_tokens': 95,
        'cost_usd': 0.00004,
        'latency': 1.8
    }


# ============================================================================
# Test Agent Initialization
# ============================================================================

def test_agent_initialization(outreach_agent):
    """Test that OutreachAgent initializes correctly"""
    assert outreach_agent.agent_name == "OutreachAgent"
    assert "email" in outreach_agent.supported_channels
    assert "linkedin" in outreach_agent.supported_channels
    assert "phone" in outreach_agent.supported_channels
    assert "professional" in outreach_agent.tone_guidelines
    assert "friendly" in outreach_agent.tone_guidelines


def test_agent_tone_guidelines(outreach_agent):
    """Test that tone guidelines are properly defined"""
    assert len(outreach_agent.tone_guidelines) >= 4
    assert outreach_agent.tone_guidelines["professional"] is not None
    assert outreach_agent.tone_guidelines["friendly"] is not None
    assert outreach_agent.tone_guidelines["enthusiastic"] is not None
    assert outreach_agent.tone_guidelines["casual"] is not None


# ============================================================================
# Test Message Generation
# ============================================================================

@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.save_to_dynamodb')
@patch('agents.outreach_agent.update_dynamodb_item')
def test_generate_outreach_email_success(
    mock_update,
    mock_save,
    mock_bedrock,
    outreach_agent,
    sample_job_details,
    sample_candidates,
    mock_nova_response_email
):
    """Test successful email outreach generation"""
    # Setup mocks
    mock_bedrock.return_value = mock_nova_response_email
    mock_save.return_value = {'success': True}
    mock_update.return_value = {'success': True}
    
    # Generate outreach
    result = outreach_agent.generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidates=sample_candidates,
        outreach_parameters={
            "channel": "email",
            "tone": "professional",
            "max_length": 250
        }
    )
    
    # Verify result
    assert result['status'] == 'success'
    assert result['data']['messages_generated'] == 2
    assert len(result['data']['outreach_results']) == 2
    
    # Verify first message
    first_message = result['data']['outreach_results'][0]
    assert first_message['candidate_id'] == 'cand-001'
    assert first_message['channel'] == 'email'
    assert first_message['subject'] is not None
    assert first_message['message'] is not None
    assert first_message['status'] == 'sent'
    
    # Verify summary
    summary = result['data']['outreach_summary']
    assert summary['total_candidates'] == 2
    assert summary['messages_generated'] == 2
    assert summary['channel'] == 'email'
    assert summary['tone'] == 'professional'
    assert summary['total_cost_usd'] > 0


@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.save_to_dynamodb')
@patch('agents.outreach_agent.update_dynamodb_item')
def test_generate_outreach_linkedin_success(
    mock_update,
    mock_save,
    mock_bedrock,
    outreach_agent,
    sample_job_details,
    sample_candidate,
    mock_nova_response_linkedin
):
    """Test successful LinkedIn InMail generation"""
    # Setup mocks
    mock_bedrock.return_value = mock_nova_response_linkedin
    mock_save.return_value = {'success': True}
    mock_update.return_value = {'success': True}
    
    # Generate outreach
    result = outreach_agent.generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidates=[sample_candidate],
        outreach_parameters={
            "channel": "linkedin",
            "tone": "friendly",
            "max_length": 150
        }
    )
    
    # Verify result
    assert result['status'] == 'success'
    assert result['data']['messages_generated'] == 1
    
    # Verify message
    message = result['data']['outreach_results'][0]
    assert message['channel'] == 'linkedin'
    assert message['message'] is not None
    # LinkedIn doesn't have subject line
    assert len(message['message'].split()) <= 200  # LinkedIn limit


def test_generate_outreach_invalid_channel(
    outreach_agent,
    sample_job_details,
    sample_candidate
):
    """Test that invalid channel returns error"""
    result = outreach_agent.generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidates=[sample_candidate],
        outreach_parameters={"channel": "telegram"}
    )
    
    assert result['status'] == 'error'
    assert 'Unsupported channel' in result['error']
    assert result['error_code'] == 'InvalidChannel'


@patch('agents.outreach_agent.invoke_bedrock')
def test_generate_outreach_nova_failure(
    mock_bedrock,
    outreach_agent,
    sample_job_details,
    sample_candidate
):
    """Test handling of Nova invocation failure"""
    # Setup mock to fail
    mock_bedrock.return_value = {
        'success': False,
        'error': 'ThrottlingException'
    }
    
    # Generate outreach
    result = outreach_agent.generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidates=[sample_candidate],
        outreach_parameters={"channel": "email"}
    )
    
    # Should still return success but with 0 messages generated
    assert result['status'] == 'success'
    assert result['data']['messages_generated'] == 0


# ============================================================================
# Test Personalized Message Generation
# ============================================================================

@patch('agents.outreach_agent.invoke_bedrock')
def test_generate_personalized_message_email(
    mock_bedrock,
    outreach_agent,
    sample_candidate,
    sample_job_details,
    mock_nova_response_email
):
    """Test personalized email message generation"""
    mock_bedrock.return_value = mock_nova_response_email
    
    result = outreach_agent.generate_personalized_message(
        candidate=sample_candidate,
        job_details=sample_job_details,
        channel="email",
        tone="professional",
        max_length=250,
        include_salary=True
    )
    
    assert result['success'] is True
    assert result['subject'] is not None
    assert result['message'] is not None
    assert result['personalization_score'] > 0
    assert result['input_tokens'] > 0
    assert result['output_tokens'] > 0
    assert result['cost_usd'] > 0


@patch('agents.outreach_agent.invoke_bedrock')
def test_generate_personalized_message_different_tones(
    mock_bedrock,
    outreach_agent,
    sample_candidate,
    sample_job_details,
    mock_nova_response_email
):
    """Test message generation with different tones"""
    mock_bedrock.return_value = mock_nova_response_email
    
    tones = ["professional", "friendly", "enthusiastic", "casual"]
    
    for tone in tones:
        result = outreach_agent.generate_personalized_message(
            candidate=sample_candidate,
            job_details=sample_job_details,
            channel="email",
            tone=tone,
            max_length=250,
            include_salary=False
        )
        
        assert result['success'] is True
        assert result['metadata']['tone'] == tone


# ============================================================================
# Test System Prompt Building
# ============================================================================

def test_build_system_prompt_email(outreach_agent):
    """Test system prompt building for email"""
    prompt = outreach_agent._build_system_prompt("email", "professional")
    
    assert "email" in prompt.lower()
    assert "professional" in prompt.lower()
    assert "subject" in prompt.lower()
    assert "JSON" in prompt


def test_build_system_prompt_linkedin(outreach_agent):
    """Test system prompt building for LinkedIn"""
    prompt = outreach_agent._build_system_prompt("linkedin", "friendly")
    
    assert "linkedin" in prompt.lower()
    assert "inmail" in prompt.lower()
    assert "friendly" in prompt.lower()
    assert "200 words" in prompt.lower()


def test_build_system_prompt_phone(outreach_agent):
    """Test system prompt building for phone"""
    prompt = outreach_agent._build_system_prompt("phone", "professional")
    
    assert "phone" in prompt.lower()
    assert "script" in prompt.lower()
    assert "brief" in prompt.lower()


# ============================================================================
# Test User Prompt Building
# ============================================================================

def test_build_user_prompt_basic(outreach_agent, sample_candidate, sample_job_details):
    """Test user prompt building with basic information"""
    prompt = outreach_agent._build_user_prompt(
        candidate=sample_candidate,
        job_details=sample_job_details,
        max_length=250,
        include_salary=False
    )
    
    assert sample_candidate['name'] in prompt
    assert sample_candidate['current_title'] in prompt
    assert sample_job_details['title'] in prompt
    assert sample_job_details['company'] in prompt
    assert "250 words" in prompt


def test_build_user_prompt_with_salary(outreach_agent, sample_candidate, sample_job_details):
    """Test user prompt building with salary information"""
    prompt = outreach_agent._build_user_prompt(
        candidate=sample_candidate,
        job_details=sample_job_details,
        max_length=250,
        include_salary=True
    )
    
    assert "140,000" in prompt or "140000" in prompt
    assert "180,000" in prompt or "180000" in prompt


def test_build_user_prompt_with_strengths(outreach_agent, sample_candidate, sample_job_details):
    """Test that candidate strengths are included in prompt"""
    prompt = outreach_agent._build_user_prompt(
        candidate=sample_candidate,
        job_details=sample_job_details,
        max_length=250,
        include_salary=False
    )
    
    # Should include at least some strengths
    assert "Python" in prompt or "AWS" in prompt


# ============================================================================
# Test Nova Response Parsing
# ============================================================================

def test_parse_nova_response_valid_json(outreach_agent):
    """Test parsing valid JSON response"""
    json_response = json.dumps({
        "subject": "Great Opportunity",
        "message": "Hi there, this is a test message.",
        "call_to_action": "Reply to schedule a call"
    })
    
    result = outreach_agent._parse_nova_response(json_response, "email")
    
    assert result['subject'] == "Great Opportunity"
    assert result['message'] == "Hi there, this is a test message."
    assert result['call_to_action'] == "Reply to schedule a call"


def test_parse_nova_response_invalid_json(outreach_agent):
    """Test parsing invalid JSON (fallback to raw text)"""
    raw_response = "Subject: Test Subject\n\nThis is the message body."
    
    result = outreach_agent._parse_nova_response(raw_response, "email")
    
    assert result['subject'] == "Test Subject"
    assert "message body" in result['message']


def test_parse_nova_response_linkedin_no_subject(outreach_agent):
    """Test parsing LinkedIn response (no subject needed)"""
    json_response = json.dumps({
        "message": "Hi, this is a LinkedIn message.",
        "call_to_action": "Connect with me"
    })
    
    result = outreach_agent._parse_nova_response(json_response, "linkedin")
    
    assert result['subject'] is None
    assert result['message'] == "Hi, this is a LinkedIn message."



# ============================================================================
# Test Personalization Score Calculation
# ============================================================================

def test_calculate_personalization_score_high(outreach_agent, sample_candidate):
    """Test personalization score calculation for highly personalized message"""
    message = """Hi Alice Johnson,

I was impressed by your Python expertise and AWS certification. Your 7 years of experience 
at CloudTech Inc building scalable systems is exactly what we're looking for. Your strong 
React skills would be perfect for our frontend needs.

Would you be interested in discussing this opportunity?"""
    
    score = outreach_agent._calculate_personalization_score(message, sample_candidate)
    
    # Should score high because it mentions:
    # - Name (Alice Johnson)
    # - Skills (Python, AWS, React)
    # - Company (CloudTech Inc)
    # - No generic phrases
    assert score >= 0.7


def test_calculate_personalization_score_low(outreach_agent, sample_candidate):
    """Test personalization score calculation for generic message"""
    message = """Dear Sir/Madam,

We are looking for great candidates for a competitive salary. This is a great opportunity 
to join our team. Please apply if interested.

To whom it may concern."""
    
    score = outreach_agent._calculate_personalization_score(message, sample_candidate)
    
    # Should score low because:
    # - No name mentioned
    # - No specific skills
    # - Generic phrases used
    assert score < 0.5


def test_calculate_personalization_score_medium(outreach_agent, sample_candidate):
    """Test personalization score calculation for moderately personalized message"""
    message = """Hi Alice,

I noticed your Python and AWS skills. We have an exciting opportunity that might interest you.

Let me know if you'd like to learn more."""
    
    score = outreach_agent._calculate_personalization_score(message, sample_candidate)
    
    # Should score medium because:
    # - Name mentioned (first name only)
    # - Some skills mentioned
    # - No company mentioned
    # - No generic phrases
    assert 0.4 <= score <= 0.8


def test_calculate_personalization_score_no_candidate_info(outreach_agent):
    """Test personalization score with minimal candidate information"""
    minimal_candidate = {
        "name": "John Doe",
        "strengths": [],
        "current_title": "",
        "current_company": ""
    }
    
    message = "Hi John, we have an opportunity for you."
    
    score = outreach_agent._calculate_personalization_score(message, minimal_candidate)
    
    # Should still give some score for name mention
    assert score > 0


# ============================================================================
# Test Outreach Message Saving
# ============================================================================

@patch('agents.outreach_agent.save_to_dynamodb')
@patch('agents.outreach_agent.update_dynamodb_item')
def test_save_outreach_message_success(mock_update, mock_save, outreach_agent):
    """Test successful saving of outreach message"""
    mock_save.return_value = {'success': True}
    mock_update.return_value = {'success': True}
    
    result = outreach_agent._save_outreach_message(
        candidate_id="cand-001",
        job_id="job-123",
        message="Test message",
        subject="Test Subject",
        channel="email",
        metadata={"tone": "professional"}
    )
    
    assert result['success'] is True
    
    # Verify save_to_dynamodb was called
    assert mock_save.called
    call_args = mock_save.call_args[0]
    assert call_args[0] == Config.INTERACTIONS_TABLE
    
    # Verify update_dynamodb_item was called
    assert mock_update.called


@patch('agents.outreach_agent.save_to_dynamodb')
def test_save_outreach_message_failure(mock_save, outreach_agent):
    """Test handling of save failure"""
    mock_save.return_value = {
        'success': False,
        'error': 'DynamoDB error'
    }
    
    result = outreach_agent._save_outreach_message(
        candidate_id="cand-001",
        job_id="job-123",
        message="Test message",
        subject="Test Subject",
        channel="email",
        metadata={}
    )
    
    assert result['success'] is False


# ============================================================================
# Test Follow-up Message Generation
# ============================================================================

@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.get_from_dynamodb')
def test_generate_follow_up_message_success(
    mock_get,
    mock_bedrock,
    outreach_agent,
    sample_candidate
):
    """Test successful follow-up message generation"""
    # Setup mocks
    mock_get.return_value = {
        'candidateId': 'cand-001',
        'name': 'Alice Johnson',
        'jobTitle': 'Senior Software Engineer'
    }
    
    mock_bedrock.return_value = {
        'success': True,
        'content': json.dumps({
            "subject": "Following up on TechCorp opportunity",
            "message": "Hi Alice, I wanted to follow up on my previous message about the Senior Engineer role. I understand you're busy. Would you have 10 minutes this week for a quick chat?"
        }),
        'input_tokens': 300,
        'output_tokens': 80,
        'cost_usd': 0.00003
    }
    
    # Generate follow-up
    result = outreach_agent.generate_follow_up_message(
        candidate_id="cand-001",
        job_id="job-123",
        original_message="Hi Alice, I wanted to reach out about an opportunity...",
        days_since_outreach=7,
        tone="friendly"
    )
    
    assert result['status'] == 'success'
    assert result['data']['subject'] is not None
    assert result['data']['message'] is not None
    assert result['data']['follow_up_number'] == 1
    assert result['data']['recommended_wait_days'] == 7


@patch('agents.outreach_agent.get_from_dynamodb')
def test_generate_follow_up_message_candidate_not_found(mock_get, outreach_agent):
    """Test follow-up generation when candidate not found"""
    mock_get.return_value = None
    
    result = outreach_agent.generate_follow_up_message(
        candidate_id="cand-999",
        job_id="job-123",
        original_message="Test message",
        days_since_outreach=7
    )
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'CandidateNotFound'


@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.get_from_dynamodb')
def test_generate_follow_up_message_nova_failure(
    mock_get,
    mock_bedrock,
    outreach_agent
):
    """Test follow-up generation when Nova fails"""
    mock_get.return_value = {
        'candidateId': 'cand-001',
        'name': 'Alice Johnson'
    }
    
    mock_bedrock.return_value = {
        'success': False,
        'error': 'Service unavailable'
    }
    
    result = outreach_agent.generate_follow_up_message(
        candidate_id="cand-001",
        job_id="job-123",
        original_message="Test",
        days_since_outreach=7
    )
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'NovaInvocationFailed'


# ============================================================================
# Test Batch Outreach Generation
# ============================================================================

@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.get_from_dynamodb')
@patch('agents.outreach_agent.save_to_dynamodb')
@patch('agents.outreach_agent.update_dynamodb_item')
def test_batch_generate_outreach_success(
    mock_update,
    mock_save,
    mock_get,
    mock_bedrock,
    outreach_agent,
    sample_job_details,
    mock_nova_response_email
):
    """Test batch outreach generation"""
    # Setup mocks
    mock_get.side_effect = [
        {
            'candidateId': 'cand-001',
            'name': 'Alice Johnson',
            'strengths': ['Python expert'],
            'screening_score': 0.92
        },
        {
            'candidateId': 'cand-002',
            'name': 'Bob Smith',
            'strengths': ['AWS expert'],
            'screening_score': 0.85
        }
    ]
    
    mock_bedrock.return_value = mock_nova_response_email
    mock_save.return_value = {'success': True}
    mock_update.return_value = {'success': True}
    
    # Generate batch outreach
    result = outreach_agent.batch_generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidate_ids=["cand-001", "cand-002"],
        outreach_parameters={"channel": "email", "tone": "professional"}
    )
    
    assert result['status'] == 'success'
    assert result['data']['messages_generated'] == 2


@patch('agents.outreach_agent.get_from_dynamodb')
def test_batch_generate_outreach_some_not_found(
    mock_get,
    outreach_agent,
    sample_job_details
):
    """Test batch outreach when some candidates not found"""
    # First candidate found, second not found
    mock_get.side_effect = [
        {
            'candidateId': 'cand-001',
            'name': 'Alice Johnson',
            'strengths': ['Python expert'],
            'screening_score': 0.92
        },
        None  # Second candidate not found
    ]
    
    result = outreach_agent.batch_generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidate_ids=["cand-001", "cand-002"]
    )
    
    # Should still process the found candidate
    # Result depends on whether Nova is mocked in this test


# ============================================================================
# Test Outreach Analytics
# ============================================================================

def test_get_outreach_analytics_success(outreach_agent):
    """Test retrieving outreach analytics"""
    result = outreach_agent.get_outreach_analytics(
        job_id="job-123",
        days=30
    )
    
    assert result['status'] == 'success'
    assert 'job_id' in result['data']
    assert 'period_days' in result['data']
    assert 'total_outreach_sent' in result['data']
    assert 'response_rate' in result['data']
    assert 'by_channel' in result['data']
    assert 'by_tone' in result['data']


def test_get_outreach_analytics_different_periods(outreach_agent):
    """Test analytics for different time periods"""
    periods = [7, 14, 30, 90]
    
    for days in periods:
        result = outreach_agent.get_outreach_analytics(
            job_id="job-123",
            days=days
        )
        
        assert result['status'] == 'success'
        assert result['data']['period_days'] == days


# ============================================================================
# Test Lambda Handler
# ============================================================================

@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.save_to_dynamodb')
@patch('agents.outreach_agent.update_dynamodb_item')
def test_lambda_handler_generate_outreach(
    mock_update,
    mock_save,
    mock_bedrock,
    mock_nova_response_email,
    sample_job_details,
    sample_candidate
):
    """Test Lambda handler for generate_outreach operation"""
    from agents.outreach_agent import lambda_handler
    
    mock_bedrock.return_value = mock_nova_response_email
    mock_save.return_value = {'success': True}
    mock_update.return_value = {'success': True}
    
    event = {
        'operation': 'generate_outreach',
        'job_id': 'job-123',
        'job_details': sample_job_details,
        'candidates': [sample_candidate],
        'outreach_parameters': {
            'channel': 'email',
            'tone': 'professional'
        }
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'
    assert result['data']['messages_generated'] >= 0


@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.get_from_dynamodb')
def test_lambda_handler_generate_follow_up(
    mock_get,
    mock_bedrock
):
    """Test Lambda handler for generate_follow_up operation"""
    from agents.outreach_agent import lambda_handler
    
    mock_get.return_value = {
        'candidateId': 'cand-001',
        'name': 'Alice Johnson'
    }
    
    mock_bedrock.return_value = {
        'success': True,
        'content': json.dumps({
            "subject": "Follow-up",
            "message": "Hi Alice, following up..."
        }),
        'input_tokens': 200,
        'output_tokens': 50,
        'cost_usd': 0.00002
    }
    
    event = {
        'operation': 'generate_follow_up',
        'candidate_id': 'cand-001',
        'job_id': 'job-123',
        'original_message': 'Original message',
        'days_since_outreach': 7,
        'tone': 'friendly'
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'


def test_lambda_handler_get_analytics():
    """Test Lambda handler for get_outreach_analytics operation"""
    from agents.outreach_agent import lambda_handler
    
    event = {
        'operation': 'get_outreach_analytics',
        'job_id': 'job-123',
        'days': 30
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'
    assert 'job_id' in result['data']


def test_lambda_handler_unknown_operation():
    """Test Lambda handler with unknown operation"""
    from agents.outreach_agent import lambda_handler
    
    event = {
        'operation': 'unknown_operation'
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'UnknownOperation'


# ============================================================================
# Integration Tests
# ============================================================================

@patch('agents.outreach_agent.invoke_bedrock')
@patch('agents.outreach_agent.save_to_dynamodb')
@patch('agents.outreach_agent.update_dynamodb_item')
def test_full_outreach_workflow(
    mock_update,
    mock_save,
    mock_bedrock,
    outreach_agent,
    sample_job_details,
    sample_candidates,
    mock_nova_response_email
):
    """Test complete outreach workflow from generation to saving"""
    # Setup mocks
    mock_bedrock.return_value = mock_nova_response_email
    mock_save.return_value = {'success': True}
    mock_update.return_value = {'success': True}
    
    # Generate outreach
    result = outreach_agent.generate_outreach(
        job_id="job-123",
        job_details=sample_job_details,
        candidates=sample_candidates,
        outreach_parameters={
            "channel": "email",
            "tone": "professional",
            "max_length": 250,
            "include_salary": True
        }
    )
    
    # Verify complete workflow
    assert result['status'] == 'success'
    assert result['data']['messages_generated'] > 0
    assert result['data']['next_agent'] == 'SchedulingAgent'
    
    # Verify all candidates processed
    assert len(result['data']['outreach_results']) == len(sample_candidates)
    
    # Verify cost tracking
    assert result['data']['outreach_summary']['total_cost_usd'] > 0
    
    # Verify DynamoDB interactions
    assert mock_save.call_count >= len(sample_candidates)
    assert mock_update.call_count >= len(sample_candidates)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
