"""
Unit Tests for Sourcing Agent

Tests the SourcingAgent class methods including candidate discovery, match scoring,
Boolean search construction, ranking, and error handling.

References:
- 08_agent_specifications.md: Sourcing Agent requirements
- 16_module_build_checklist.md: Phase 4.1 testing requirements
- 17_testing_strategy.md: Testing approach and patterns

Verification Sources:
- Pytest Documentation: https://docs.pytest.org/
- Mocking AWS Services: https://docs.getmoto.org/
- Python Unit Testing Best Practices: https://realpython.com/python-testing/
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the sourcing agent
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sourcing_agent import SourcingAgent, lambda_handler
from shared.models import Candidate, CandidateStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sourcing_agent():
    """Create a SourcingAgent instance for testing"""
    return SourcingAgent()


@pytest.fixture
def mock_job_requirements():
    """Create mock job requirements for testing"""
    return {
        "title": "Senior Software Engineer",
        "required_skills": ["Python", "AWS", "React"],
        "preferred_skills": ["GraphQL", "Docker"],
        "experience_years": {"min": 5, "max": 10},
        "location": "Seattle, WA or Remote",
        "education": "Bachelor's in Computer Science or equivalent"
    }


@pytest.fixture
def mock_candidate_data():
    """Create mock candidate data for testing"""
    return {
        "name": "John Doe",
        "current_title": "Senior Software Engineer",
        "current_company": "Tech Corp",
        "location": "Seattle, WA",
        "experience_years": 7,
        "skills": ["Python", "AWS", "React", "Docker"],
        "education": "BS Computer Science, University of Washington",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "github_url": "https://github.com/johndoe",
        "source": "linkedin",
        "summary": "Experienced engineer with strong Python and AWS background"
    }


@pytest.fixture
def mock_sourcing_parameters():
    """Create mock sourcing parameters for testing"""
    return {
        "target_count": 50,
        "sources": ["linkedin", "github"],
        "min_match_score": 0.6
    }


# ============================================================================
# Test: Agent Initialization
# ============================================================================

def test_sourcing_agent_initialization(sourcing_agent):
    """Test that SourcingAgent initializes correctly"""
    assert sourcing_agent.agent_name == "SourcingAgent"
    assert len(sourcing_agent.supported_sources) == 5
    assert "linkedin" in sourcing_agent.supported_sources
    assert "github" in sourcing_agent.supported_sources
    
    # Check score weights
    assert sourcing_agent.score_weights["required_skills"] == 0.40
    assert sourcing_agent.score_weights["experience"] == 0.25
    assert sum(sourcing_agent.score_weights.values()) == 1.0


# ============================================================================
# Test: Calculate Match Score
# ============================================================================

def test_calculate_match_score_perfect_match(sourcing_agent, mock_candidate_data, mock_job_requirements):
    """Test match score calculation for perfect candidate"""
    score = sourcing_agent.calculate_match_score(mock_candidate_data, mock_job_requirements)
    
    # Should be high score (>0.9) since candidate has all required skills + preferred
    assert score > 0.9
    assert score <= 1.0


def test_calculate_match_score_partial_match(sourcing_agent, mock_job_requirements):
    """Test match score calculation for partial match"""
    candidate = {
        "skills": ["Python", "AWS"],  # Missing React
        "experience_years": 6,
        "location": "Seattle, WA",
        "education": "Bachelor's Degree"
    }
    
    score = sourcing_agent.calculate_match_score(candidate, mock_job_requirements)
    
    # Should be moderate score (0.6-0.8) - has 2/3 required skills
    assert 0.5 < score < 0.9


def test_calculate_match_score_weak_match(sourcing_agent, mock_job_requirements):
    """Test match score calculation for weak match"""
    candidate = {
        "skills": ["Python"],  # Only 1/3 required skills
        "experience_years": 3,  # Below minimum
        "location": "New York, NY",  # Different location
        "education": "High School"
    }
    
    score = sourcing_agent.calculate_match_score(candidate, mock_job_requirements)
    
    # Should be low score (<0.5)
    assert score < 0.5


def test_calculate_match_score_remote_location(sourcing_agent, mock_job_requirements):
    """Test that remote candidates match remote jobs"""
    candidate = {
        "skills": ["Python", "AWS", "React"],
        "experience_years": 6,
        "location": "Remote",
        "education": "Bachelor's Degree"
    }
    
    score = sourcing_agent.calculate_match_score(candidate, mock_job_requirements)
    
    # Should get full location score
    assert score > 0.8


def test_calculate_match_score_overqualified(sourcing_agent, mock_job_requirements):
    """Test scoring for overqualified candidate"""
    candidate = {
        "skills": ["Python", "AWS", "React", "GraphQL", "Docker"],
        "experience_years": 15,  # Above max (10)
        "location": "Seattle, WA",
        "education": "PhD Computer Science"
    }
    
    score = sourcing_agent.calculate_match_score(candidate, mock_job_requirements)
    
    # Should still be high but slightly penalized for over-experience
    assert 0.85 < score <= 1.0


# ============================================================================
# Test: Boolean Search Construction
# ============================================================================

def test_construct_boolean_search_basic(sourcing_agent, mock_job_requirements):
    """Test Boolean search query construction"""
    query = sourcing_agent.construct_boolean_search(mock_job_requirements)
    
    assert "Senior Software Engineer" in query
    assert "Python" in query
    assert "AWS" in query
    assert "React" in query
    assert "AND" in query


def test_construct_boolean_search_with_location(sourcing_agent):
    """Test Boolean search includes location"""
    requirements = {
        "title": "Data Scientist",
        "required_skills": ["Python", "ML"],
        "location": "San Francisco, CA"
    }
    
    query = sourcing_agent.construct_boolean_search(requirements)
    
    assert "location:" in query
    assert "San Francisco, CA" in query


def test_construct_boolean_search_remote_no_location(sourcing_agent):
    """Test Boolean search excludes location for remote jobs"""
    requirements = {
        "title": "Software Engineer",
        "required_skills": ["JavaScript"],
        "location": "Remote"
    }
    
    query = sourcing_agent.construct_boolean_search(requirements)
    
    # Should not include location filter for remote jobs
    assert "location:" not in query


# ============================================================================
# Test: Source Candidates
# ============================================================================

@patch('agents.sourcing_agent.save_to_dynamodb')
@patch('agents.sourcing_agent.invoke_bedrock')
def test_source_candidates_success(mock_bedrock, mock_save, sourcing_agent, mock_job_requirements, mock_sourcing_parameters):
    """Test successful candidate sourcing"""
    # Mock Nova response with candidate profiles
    mock_candidates = [
        {
            "name": f"Candidate {i}",
            "current_title": "Software Engineer",
            "current_company": f"Company {i}",
            "location": "Seattle, WA",
            "experience_years": 6,
            "skills": ["Python", "AWS", "React"],
            "education": "Bachelor's Degree",
            "linkedin_url": f"https://linkedin.com/in/candidate{i}",
            "source": "linkedin",
            "summary": "Experienced engineer"
        }
        for i in range(10)
    ]
    
    mock_bedrock.return_value = {
        'success': True,
        'content': json.dumps(mock_candidates),
        'input_tokens': 1000,
        'output_tokens': 3000,
        'cost_usd': 0.0024
    }
    
    mock_save.return_value = {'success': True}
    
    # Source candidates
    result = sourcing_agent.source_candidates(
        job_id='job-123',
        job_requirements=mock_job_requirements,
        sourcing_parameters=mock_sourcing_parameters
    )
    
    # Verify result
    assert result['status'] == 'success'
    assert 'candidates' in result['data']
    assert 'sourcing_summary' in result['data']
    assert result['data']['next_agent'] == 'ScreeningAgent'
    
    # Verify DynamoDB saves were called
    assert mock_save.called


@patch('agents.sourcing_agent.save_to_dynamodb')
@patch('agents.sourcing_agent.invoke_bedrock')
def test_source_candidates_nova_failure_uses_fallback(mock_bedrock, mock_save, sourcing_agent, mock_job_requirements):
    """Test that fallback candidates are generated when Nova fails"""
    # Mock Nova failure
    mock_bedrock.return_value = {
        'success': False,
        'error': 'API timeout'
    }
    
    mock_save.return_value = {'success': True}
    
    # Source candidates
    result = sourcing_agent.source_candidates(
        job_id='job-123',
        job_requirements=mock_job_requirements,
        sourcing_parameters={"target_count": 10}
    )
    
    # Should still succeed with fallback candidates
    assert result['status'] == 'success'
    assert len(result['data']['candidates']) > 0


@patch('agents.sourcing_agent.save_to_dynamodb')
@patch('agents.sourcing_agent.invoke_bedrock')
def test_source_candidates_filters_by_min_score(mock_bedrock, mock_save, sourcing_agent, mock_job_requirements):
    """Test that candidates below minimum score are filtered out"""
    # Mock candidates with varying quality
    mock_candidates = [
        {
            "name": "Strong Candidate",
            "skills": ["Python", "AWS", "React", "GraphQL"],
            "experience_years": 7,
            "location": "Seattle, WA",
            "education": "Bachelor's Degree",
            "current_title": "Senior Engineer",
            "current_company": "Tech Corp",
            "linkedin_url": "https://linkedin.com/in/strong",
            "source": "linkedin",
            "summary": "Strong match"
        },
        {
            "name": "Weak Candidate",
            "skills": ["Java"],  # Wrong skills
            "experience_years": 2,  # Too junior
            "location": "Remote",
            "education": "High School",
            "current_title": "Junior Developer",
            "current_company": "Startup",
            "linkedin_url": "https://linkedin.com/in/weak",
            "source": "linkedin",
            "summary": "Weak match"
        }
    ]
    
    mock_bedrock.return_value = {
        'success': True,
        'content': json.dumps(mock_candidates),
        'input_tokens': 500,
        'output_tokens': 1000,
        'cost_usd': 0.0012
    }
    
    mock_save.return_value = {'success': True}
    
    # Source with high minimum score
    result = sourcing_agent.source_candidates(
        job_id='job-123',
        job_requirements=mock_job_requirements,
        sourcing_parameters={"target_count": 10, "min_match_score": 0.7}
    )
    
    # Should only include strong candidate
    assert result['status'] == 'success'
    # Weak candidate should be filtered out
    assert result['data']['sourcing_summary']['candidates_meeting_criteria'] < len(mock_candidates)


# ============================================================================
# Test: Helper Methods
# ============================================================================

def test_locations_match_same_city(sourcing_agent):
    """Test location matching for same city"""
    assert sourcing_agent._locations_match("Seattle, WA", "Seattle, Washington")
    assert sourcing_agent._locations_match("New York, NY", "New York City")


def test_locations_match_different_cities(sourcing_agent):
    """Test location matching for different cities"""
    assert not sourcing_agent._locations_match("Seattle, WA", "Portland, OR")


def test_same_state_matching(sourcing_agent):
    """Test state matching"""
    assert sourcing_agent._same_state("Seattle, WA", "Spokane, WA")
    assert sourcing_agent._same_state("San Francisco, CA", "Los Angeles, CA")
    assert not sourcing_agent._same_state("Seattle, WA", "Portland, OR")


def test_evaluate_education_phd(sourcing_agent):
    """Test education evaluation for PhD"""
    score = sourcing_agent._evaluate_education("PhD Computer Science", "Bachelor's required")
    assert score == 1.0


def test_evaluate_education_masters(sourcing_agent):
    """Test education evaluation for Master's"""
    score = sourcing_agent._evaluate_education("Master's in CS", "Bachelor's required")
    assert score == 1.0


def test_evaluate_education_bachelors(sourcing_agent):
    """Test education evaluation for Bachelor's"""
    score = sourcing_agent._evaluate_education("Bachelor of Science", "Bachelor's required")
    assert score == 1.0


def test_evaluate_education_below_requirement(sourcing_agent):
    """Test education evaluation below requirement"""
    score = sourcing_agent._evaluate_education("High School", "Bachelor's required")
    assert score < 1.0


def test_rank_candidates(sourcing_agent):
    """Test candidate ranking by match score"""
    candidates = [
        {"name": "Candidate A", "match_score": 0.7},
        {"name": "Candidate B", "match_score": 0.9},
        {"name": "Candidate C", "match_score": 0.8}
    ]
    
    ranked = sourcing_agent._rank_candidates(candidates)
    
    assert ranked[0]["name"] == "Candidate B"  # Highest score
    assert ranked[1]["name"] == "Candidate C"
    assert ranked[2]["name"] == "Candidate A"  # Lowest score


def test_create_candidate_record(sourcing_agent, mock_candidate_data):
    """Test creating Candidate model from data"""
    candidate = sourcing_agent._create_candidate_record(mock_candidate_data, "job-123")
    
    assert candidate.job_id == "job-123"
    assert candidate.name == "John Doe"
    assert candidate.status == CandidateStatus.SOURCED
    assert candidate.current_title == "Senior Software Engineer"
    assert "Python" in candidate.skills


# ============================================================================
# Test: Lambda Handler
# ============================================================================

@patch('agents.sourcing_agent.SourcingAgent')
def test_lambda_handler_source_candidates(mock_agent_class):
    """Test Lambda handler for source_candidates operation"""
    mock_agent = Mock()
    mock_agent.source_candidates.return_value = {
        'status': 'success',
        'data': {'candidates_found': 50}
    }
    mock_agent_class.return_value = mock_agent
    
    event = {
        'operation': 'source_candidates',
        'job_id': 'job-123',
        'job_requirements': {'title': 'Engineer'},
        'sourcing_parameters': {'target_count': 50}
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'
    mock_agent.source_candidates.assert_called_once()


@patch('agents.sourcing_agent.SourcingAgent')
def test_lambda_handler_calculate_match_score(mock_agent_class):
    """Test Lambda handler for calculate_match_score operation"""
    mock_agent = Mock()
    mock_agent.calculate_match_score.return_value = 0.85
    mock_agent_class.return_value = mock_agent
    
    event = {
        'operation': 'calculate_match_score',
        'candidate_data': {'skills': ['Python']},
        'job_requirements': {'required_skills': ['Python']}
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'
    assert result['data']['match_score'] == 0.85


@patch('agents.sourcing_agent.SourcingAgent')
def test_lambda_handler_construct_boolean_search(mock_agent_class):
    """Test Lambda handler for construct_boolean_search operation"""
    mock_agent = Mock()
    mock_agent.construct_boolean_search.return_value = "Engineer AND Python"
    mock_agent_class.return_value = mock_agent
    
    event = {
        'operation': 'construct_boolean_search',
        'job_requirements': {'title': 'Engineer', 'required_skills': ['Python']}
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'success'
    assert 'boolean_query' in result['data']


@patch('agents.sourcing_agent.SourcingAgent')
def test_lambda_handler_unknown_operation(mock_agent_class):
    """Test Lambda handler with unknown operation"""
    mock_agent_class.return_value = Mock()
    
    event = {
        'operation': 'unknown_operation'
    }
    
    result = lambda_handler(event, None)
    
    assert result['status'] == 'error'
    assert result['error_code'] == 'UnknownOperation'


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=agents.sourcing_agent', '--cov-report=term-missing'])
