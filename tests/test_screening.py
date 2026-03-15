"""
Unit tests for Screening Agent

Tests cover:
- Screening score calculation
- Pass/fail determination
- Education evaluation
- Cultural fit assessment
- Candidate ranking
- Strengths/concerns analysis
- Lambda handler

Run with: pytest tests/test_screening.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from agents.screening_agent import ScreeningAgent, lambda_handler


class TestScreeningAgent:
    """Test suite for ScreeningAgent class"""
    
    @pytest.fixture
    def agent(self):
        """Create ScreeningAgent instance for testing"""
        return ScreeningAgent()
    
    @pytest.fixture
    def sample_job_requirements(self):
        """Sample job requirements for testing"""
        return {
            "title": "Senior Software Engineer",
            "required_skills": ["Python", "AWS", "React"],
            "preferred_skills": ["GraphQL", "Docker"],
            "experience_years": {"min": 5, "max": 10},
            "education": "Bachelor's in Computer Science",
            "location": "Seattle, WA or Remote"
        }
    
    @pytest.fixture
    def perfect_candidate(self):
        """Perfect match candidate"""
        return {
            "candidate_id": "C001",
            "name": "Alice Perfect",
            "skills": ["Python", "AWS", "React", "GraphQL", "Docker"],
            "experience_years": 7,
            "education": "BS Computer Science, MIT",
            "location": "Seattle, WA",
            "linkedin_url": "https://linkedin.com/in/alice",
            "github_url": "https://github.com/alice",
            "notes": "Excellent full-stack engineer with strong AWS background"
        }
    
    @pytest.fixture
    def weak_candidate(self):
        """Weak match candidate"""
        return {
            "candidate_id": "C002",
            "name": "Bob Weak",
            "skills": ["Python"],
            "experience_years": 2,
            "education": "High School",
            "location": "New York, NY",
            "notes": ""
        }
    
    @pytest.fixture
    def moderate_candidate(self):
        """Moderate match candidate"""
        return {
            "candidate_id": "C003",
            "name": "Carol Moderate",
            "skills": ["Python", "AWS"],
            "experience_years": 5,
            "education": "Bachelor's Computer Science",
            "location": "Remote",
            "linkedin_url": "https://linkedin.com/in/carol",
            "notes": "Solid backend experience"
        }
    
    # Test: Agent Initialization
    
    def test_agent_initialization(self, agent):
        """Test agent initializes with correct configuration"""
        assert agent.agent_name == "ScreeningAgent"
        assert agent.agent_role == "Candidate Qualification Evaluator"
        assert agent.score_weights["required_skills"] == 0.35
        assert agent.score_weights["experience"] == 0.25
        assert agent.score_weights["education"] == 0.15
        assert agent.score_weights["preferred_skills"] == 0.15
        assert agent.score_weights["cultural_fit"] == 0.10
        assert sum(agent.score_weights.values()) == 1.0
    
    # Test: Screening Score Calculation
    
    def test_calculate_screening_score_perfect_match(
        self, agent, perfect_candidate, sample_job_requirements
    ):
        """Test scoring for perfect match candidate"""
        score, breakdown = agent.calculate_screening_score(
            perfect_candidate,
            sample_job_requirements
        )
        
        assert score >= 0.95  # Should be near perfect
        assert breakdown["required_skills"] == 1.0  # All required skills
        assert breakdown["experience"] == 1.0  # Experience in range
        assert breakdown["education"] >= 0.9  # Has Bachelor's
        assert breakdown["preferred_skills"] == 1.0  # All preferred skills
        assert breakdown["cultural_fit"] > 0.5  # Has indicators
    
    def test_calculate_screening_score_weak_match(
        self, agent, weak_candidate, sample_job_requirements
    ):
        """Test scoring for weak match candidate"""
        score, breakdown = agent.calculate_screening_score(
            weak_candidate,
            sample_job_requirements
        )
        
        assert score < 0.50  # Should be low score
        assert breakdown["required_skills"] < 0.5  # Missing most required skills
        assert breakdown["experience"] < 0.5  # Under-qualified
        assert breakdown["education"] < 0.5  # Education below requirement
    
    def test_calculate_screening_score_moderate_match(
        self, agent, moderate_candidate, sample_job_requirements
    ):
        """Test scoring for moderate match candidate"""
        score, breakdown = agent.calculate_screening_score(
            moderate_candidate,
            sample_job_requirements
        )
        
        assert 0.60 <= score <= 0.80  # Should be moderate score
        assert breakdown["required_skills"] < 1.0  # Missing some required skills
        assert breakdown["experience"] == 1.0  # Experience at minimum
    
    def test_calculate_screening_score_overqualified(
        self, agent, sample_job_requirements
    ):
        """Test scoring for overqualified candidate"""
        overqualified = {
            "candidate_id": "C004",
            "skills": ["Python", "AWS", "React"],
            "experience_years": 20,  # Way over max of 10
            "education": "PhD Computer Science",
            "location": "Remote"
        }
        
        score, breakdown = agent.calculate_screening_score(
            overqualified,
            sample_job_requirements
        )
        
        # Should have slight penalty for being overqualified
        assert breakdown["experience"] < 1.0
        assert breakdown["experience"] >= 0.5  # But not too harsh
    
    # Test: Pass/Fail Determination
    
    def test_should_pass_screening_above_threshold(self, agent):
        """Test pass determination when above threshold"""
        passed, reason = agent.should_pass_screening(
            overall_score=0.85,
            score_breakdown={"required_skills": 1.0},
            pass_threshold=0.70,
            require_all_must_haves=True
        )
        
        assert passed is True
        assert reason == "Passed screening"
    
    def test_should_pass_screening_below_threshold(self, agent):
        """Test fail determination when below threshold"""
        passed, reason = agent.should_pass_screening(
            overall_score=0.65,
            score_breakdown={"required_skills": 1.0},
            pass_threshold=0.70,
            require_all_must_haves=True
        )
        
        assert passed is False
        assert "Below overall threshold" in reason
    
    def test_should_pass_screening_missing_required_skills(self, agent):
        """Test fail determination when missing required skills"""
        passed, reason = agent.should_pass_screening(
            overall_score=0.75,
            score_breakdown={"required_skills": 0.67},  # Missing 33%
            pass_threshold=0.70,
            require_all_must_haves=True
        )
        
        assert passed is False
        assert "Missing" in reason and "required skills" in reason
    
    def test_should_pass_screening_without_must_haves_requirement(self, agent):
        """Test pass when not requiring all must-haves"""
        passed, reason = agent.should_pass_screening(
            overall_score=0.75,
            score_breakdown={"required_skills": 0.67},
            pass_threshold=0.70,
            require_all_must_haves=False  # Don't require all
        )
        
        assert passed is True
        assert reason == "Passed screening"

    
    # Test: Education Evaluation
    
    def test_evaluate_education_bachelor_meets_bachelor(self, agent):
        """Test Bachelor's meets Bachelor's requirement"""
        score = agent._evaluate_education(
            "Bachelor's Computer Science",
            "Bachelor's in Computer Science"
        )
        assert score == 1.0
    
    def test_evaluate_education_masters_exceeds_bachelor(self, agent):
        """Test Master's exceeds Bachelor's requirement"""
        score = agent._evaluate_education(
            "Master's Computer Science",
            "Bachelor's in Computer Science"
        )
        assert score == 1.0
    
    def test_evaluate_education_bachelor_below_masters(self, agent):
        """Test Bachelor's below Master's requirement"""
        score = agent._evaluate_education(
            "Bachelor's Computer Science",
            "Master's in Computer Science"
        )
        assert score < 1.0
        assert score > 0.5  # Partial credit
    
    def test_evaluate_education_phd_highest(self, agent):
        """Test PhD is highest education level"""
        score = agent._evaluate_education(
            "PhD Computer Science",
            "Bachelor's in Computer Science"
        )
        assert score == 1.0
    
    def test_evaluate_education_no_requirement(self, agent):
        """Test full score when no education requirement"""
        score = agent._evaluate_education(
            "High School",
            ""
        )
        assert score == 1.0
    
    # Test: Cultural Fit Assessment
    
    def test_assess_cultural_fit_high_indicators(self, agent):
        """Test cultural fit with many positive indicators"""
        candidate = {
            "notes": "Great team player",
            "github_url": "https://github.com/user",
            "linkedin_url": "https://linkedin.com/in/user",
            "location": "Remote",
            "experience_years": 7
        }
        
        score = agent._assess_cultural_fit(candidate, [])
        assert score >= 0.8  # Should have 4-5 indicators
    
    def test_assess_cultural_fit_low_indicators(self, agent):
        """Test cultural fit with few indicators"""
        candidate = {
            "notes": "",
            "location": "New York",
            "experience_years": 1
        }
        
        score = agent._assess_cultural_fit(candidate, [])
        assert score <= 0.4  # Should have 0-2 indicators
    
    # Test: Strengths and Concerns Analysis
    
    def test_analyze_candidate_profile_strengths(
        self, agent, perfect_candidate, sample_job_requirements
    ):
        """Test extraction of candidate strengths"""
        score, breakdown = agent.calculate_screening_score(
            perfect_candidate,
            sample_job_requirements
        )
        
        strengths, concerns = agent._analyze_candidate_profile(
            perfect_candidate,
            sample_job_requirements,
            breakdown
        )
        
        assert len(strengths) > 0
        assert any("required skills" in s.lower() for s in strengths)
        assert len(concerns) == 0  # Perfect candidate has no concerns
    
    def test_analyze_candidate_profile_concerns(
        self, agent, weak_candidate, sample_job_requirements
    ):
        """Test extraction of candidate concerns"""
        score, breakdown = agent.calculate_screening_score(
            weak_candidate,
            sample_job_requirements
        )
        
        strengths, concerns = agent._analyze_candidate_profile(
            weak_candidate,
            sample_job_requirements,
            breakdown
        )
        
        assert len(concerns) > 0
        assert any("missing" in c.lower() for c in concerns)
    
    # Test: Recommendation Generation
    
    def test_generate_recommendation_strong_match(self, agent):
        """Test recommendation for strong match"""
        recommendation = agent._generate_recommendation(
            0.90,
            {"required_skills": 1.0, "experience": 1.0}
        )
        assert "strong match" in recommendation.lower()
        assert "immediately" in recommendation.lower()
    
    def test_generate_recommendation_good_match(self, agent):
        """Test recommendation for good match"""
        recommendation = agent._generate_recommendation(
            0.78,
            {"required_skills": 0.9, "experience": 0.8}
        )
        assert "good match" in recommendation.lower()
    
    def test_generate_recommendation_acceptable_match(self, agent):
        """Test recommendation for acceptable match"""
        recommendation = agent._generate_recommendation(
            0.72,
            {"required_skills": 0.8, "experience": 0.7}
        )
        assert "acceptable" in recommendation.lower()
    
    def test_generate_recommendation_below_threshold(self, agent):
        """Test recommendation for below threshold"""
        recommendation = agent._generate_recommendation(
            0.65,
            {"required_skills": 0.6, "experience": 0.6}
        )
        assert "below threshold" in recommendation.lower()
        assert "do not proceed" in recommendation.lower()
    
    # Test: Confidence Calculation
    
    def test_calculate_confidence_consistent_scores(self, agent):
        """Test confidence with consistent scores"""
        breakdown = {
            "required_skills": 0.9,
            "experience": 0.9,
            "education": 0.9,
            "preferred_skills": 0.9,
            "cultural_fit": 0.9
        }
        
        confidence = agent._calculate_confidence(breakdown)
        assert confidence >= 0.9  # High confidence for consistent scores
    
    def test_calculate_confidence_varied_scores(self, agent):
        """Test confidence with varied scores"""
        breakdown = {
            "required_skills": 1.0,
            "experience": 0.3,
            "education": 0.8,
            "preferred_skills": 0.2,
            "cultural_fit": 0.6
        }
        
        confidence = agent._calculate_confidence(breakdown)
        assert confidence < 0.8  # Lower confidence for varied scores
    
    # Test: Screening Summary Generation
    
    def test_generate_screening_summary(self, agent):
        """Test screening summary generation"""
        qualified = [
            {"overall_score": 0.85, "concerns": []},
            {"overall_score": 0.78, "concerns": []},
            {"overall_score": 0.72, "concerns": []}
        ]
        
        disqualified = [
            {"overall_score": 0.65, "concerns": ["Missing required skills: React"]},
            {"overall_score": 0.60, "concerns": ["Missing required skills: AWS"]}
        ]
        
        summary = agent._generate_screening_summary(
            qualified,
            disqualified,
            {}
        )
        
        assert summary["pass_rate"] == 0.6  # 3/5
        assert summary["average_score"] > 0.70
        assert summary["top_score"] == 0.85
        assert len(summary["common_gaps"]) >= 0
    
    def test_generate_screening_summary_no_qualified(self, agent):
        """Test summary when no candidates qualified"""
        summary = agent._generate_screening_summary([], [], {})
        
        assert summary["pass_rate"] == 0.0
        assert summary["average_score"] == 0.0
        assert summary["top_score"] == 0.0
    
    # Test: Full Screening Workflow
    
    @patch('agents.screening_agent.save_to_dynamodb')
    def test_screen_candidates_success(
        self, mock_save, agent, sample_job_requirements, perfect_candidate, weak_candidate
    ):
        """Test complete screening workflow"""
        candidates = [perfect_candidate, weak_candidate]
        
        result = agent.screen_candidates(
            job_id="test_job_001",
            job_requirements=sample_job_requirements,
            candidates=candidates,
            screening_parameters={"pass_threshold": 0.70, "top_n": 10}
        )
        
        assert result["status"] == "success"
        assert result["candidates_screened"] == 2
        assert result["qualified_candidates"] >= 1  # At least perfect candidate
        assert len(result["top_candidates"]) >= 1
        assert result["top_candidates"][0]["rank"] == 1
        assert "next_agent" in result
        assert result["next_agent"] == "OutreachAgent"
    
    @patch('agents.screening_agent.save_to_dynamodb')
    def test_screen_candidates_ranking(
        self, mock_save, agent, sample_job_requirements
    ):
        """Test candidates are ranked correctly"""
        candidates = [
            {
                "candidate_id": "C1",
                "skills": ["Python", "AWS", "React"],
                "experience_years": 7,
                "education": "BS Computer Science",
                "location": "Remote"
            },
            {
                "candidate_id": "C2",
                "skills": ["Python", "AWS", "React", "GraphQL", "Docker"],
                "experience_years": 8,
                "education": "MS Computer Science",
                "location": "Seattle, WA"
            },
            {
                "candidate_id": "C3",
                "skills": ["Python", "AWS"],
                "experience_years": 5,
                "education": "BS Computer Science",
                "location": "Remote"
            }
        ]
        
        result = agent.screen_candidates(
            job_id="test_job_001",
            job_requirements=sample_job_requirements,
            candidates=candidates,
            screening_parameters={"pass_threshold": 0.60, "top_n": 10}
        )
        
        # C2 should rank highest (most skills, best education)
        top_candidates = result["top_candidates"]
        assert len(top_candidates) >= 2
        assert top_candidates[0]["candidate_id"] == "C2"
        assert top_candidates[0]["rank"] == 1
        assert top_candidates[0]["overall_score"] > top_candidates[1]["overall_score"]
    
    @patch('agents.screening_agent.save_to_dynamodb')
    def test_screen_candidates_top_n_limit(
        self, mock_save, agent, sample_job_requirements
    ):
        """Test top_n parameter limits results"""
        # Create 20 candidates
        candidates = []
        for i in range(20):
            candidates.append({
                "candidate_id": f"C{i:03d}",
                "skills": ["Python", "AWS", "React"],
                "experience_years": 7,
                "education": "BS Computer Science",
                "location": "Remote"
            })
        
        result = agent.screen_candidates(
            job_id="test_job_001",
            job_requirements=sample_job_requirements,
            candidates=candidates,
            screening_parameters={"pass_threshold": 0.60, "top_n": 5}
        )
        
        assert len(result["top_candidates"]) == 5  # Limited to top 5
        assert result["qualified_candidates"] >= 5  # But more qualified
    
    # Test: Lambda Handler
    
    @patch('agents.screening_agent.save_to_dynamodb')
    def test_lambda_handler_screen_candidates(self, mock_save):
        """Test Lambda handler for screen_candidates operation"""
        event = {
            "operation": "screen_candidates",
            "job_id": "test_job_001",
            "job_requirements": {
                "required_skills": ["Python"],
                "experience_years": {"min": 3, "max": 10}
            },
            "candidates": [
                {
                    "candidate_id": "C001",
                    "skills": ["Python", "AWS"],
                    "experience_years": 5,
                    "education": "BS Computer Science",
                    "location": "Remote"
                }
            ],
            "screening_parameters": {"pass_threshold": 0.70}
        }
        
        response = lambda_handler(event, None)
        
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["status"] == "success"
    
    def test_lambda_handler_unknown_operation(self):
        """Test Lambda handler with unknown operation"""
        event = {
            "operation": "unknown_operation"
        }
        
        response = lambda_handler(event, None)
        
        assert response["status"] == "error"
        assert "unknown operation" in response["error"].lower()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
