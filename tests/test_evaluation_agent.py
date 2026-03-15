"""
Unit tests for Evaluation Agent

Tests cover:
- Evaluation score calculation
- Hiring recommendation generation
- Interviewer consensus assessment
- Confidence calculation
- Strengths and concerns extraction
- Integration with DynamoDB

Run tests:
    pytest tests/test_evaluation_agent.py -v
    pytest tests/test_evaluation_agent.py -v --cov=agents.evaluation_agent
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from agents.evaluation_agent import EvaluationAgent


class TestEvaluationAgent:
    """Test suite for Evaluation Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create EvaluationAgent instance for testing"""
        return EvaluationAgent()
    
    @pytest.fixture
    def sample_candidate_with_feedback(self):
        """Sample candidate with interviewer feedback"""
        return {
            "candidate_id": "C001",
            "name": "Alice Johnson",
            "screening_score": 0.87,
            "sourcing_notes": "7 years React experience, AWS certified",
            "interviewer_feedback": [
                {
                    "interviewer_name": "Jane Smith",
                    "interviewer_role": "Senior Engineer",
                    "scores": {
                        "technical_skills": 4.5,
                        "problem_solving": 4.0,
                        "communication": 5.0,
                        "cultural_fit": 4.5,
                        "leadership_potential": 4.0
                    },
                    "comments": "Strong technical skills, excellent communication.",
                    "recommendation": "strong_yes",
                    "confidence": 0.9
                },
                {
                    "interviewer_name": "John Doe",
                    "interviewer_role": "Tech Lead",
                    "scores": {
                        "technical_skills": 4.0,
                        "problem_solving": 4.5,
                        "communication": 4.5,
                        "cultural_fit": 4.0,
                        "leadership_potential": 4.5
                    },
                    "comments": "Excellent problem-solving approach.",
                    "recommendation": "strong_yes",
                    "confidence": 0.85
                }
            ]
        }
    
    @pytest.fixture
    def sample_rubric(self):
        """Standard evaluation rubric"""
        return {
            "technical_skills": 0.35,
            "problem_solving": 0.25,
            "communication": 0.15,
            "cultural_fit": 0.15,
            "leadership_potential": 0.10
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initializes with correct configuration"""
        assert agent.agent_name == "EvaluationAgent"
        assert agent.agent_role == "Interview Feedback Synthesizer & Hiring Recommender"
        assert "technical_skills" in agent.evaluation_weights
        assert agent.evaluation_weights["technical_skills"] == 0.35
        assert "strong_hire" in agent.recommendation_thresholds
    
    def test_calculate_evaluation_score(self, agent, sample_candidate_with_feedback, sample_rubric):
        """Test evaluation score calculation with multiple interviewers"""
        overall_score, score_breakdown = agent.calculate_evaluation_score(
            sample_candidate_with_feedback,
            sample_rubric
        )
        
        # Check overall score is in valid range
        assert 0.0 <= overall_score <= 1.0
        
        # Check score breakdown has all categories
        assert set(score_breakdown.keys()) == set(sample_rubric.keys())
        
        # Check all category scores are in valid range
        for category, score in score_breakdown.items():
            assert 0.0 <= score <= 1.0
        
        # Check weighted calculation is correct
        expected_score = sum(
            score_breakdown[cat] * sample_rubric[cat]
            for cat in sample_rubric.keys()
        )
        assert abs(overall_score - expected_score) < 0.01
    
    def test_calculate_evaluation_score_no_feedback(self, agent, sample_rubric):
        """Test evaluation score calculation with no interviewer feedback"""
        candidate_no_feedback = {
            "candidate_id": "C002",
            "name": "Bob Smith",
            "screening_score": 0.75,
            "interviewer_feedback": []
        }
        
        overall_score, score_breakdown = agent.calculate_evaluation_score(
            candidate_no_feedback,
            sample_rubric
        )
        
        # Should fall back to screening score
        assert overall_score == 0.75
        assert all(score == 0.75 for score in score_breakdown.values())
    
    def test_generate_hiring_recommendation_strong_hire(self, agent):
        """Test hiring recommendation for strong candidate"""
        score_breakdown = {
            "technical_skills": 0.90,
            "problem_solving": 0.85,
            "communication": 0.95,
            "cultural_fit": 0.88,
            "leadership_potential": 0.82
        }
        
        consensus_analysis = {
            "unanimous": True,
            "strong_yes": 2,
            "yes": 0,
            "no": 0,
            "strong_no": 0
        }
        
        recommendation, confidence = agent.generate_hiring_recommendation(
            overall_score=0.88,
            score_breakdown=score_breakdown,
            consensus_analysis=consensus_analysis,
            decision_threshold=0.75,
            require_consensus=False
        )
        
        assert recommendation == "strong_hire"
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # High confidence for unanimous strong hire
    
    def test_generate_hiring_recommendation_no_hire(self, agent):
        """Test hiring recommendation for weak candidate"""
        score_breakdown = {
            "technical_skills": 0.50,
            "problem_solving": 0.55,
            "communication": 0.60,
            "cultural_fit": 0.50,
            "leadership_potential": 0.45
        }
        
        consensus_analysis = {
            "unanimous": False,
            "strong_yes": 0,
            "yes": 0,
            "no": 2,
            "strong_no": 0
        }
        
        recommendation, confidence = agent.generate_hiring_recommendation(
            overall_score=0.52,
            score_breakdown=score_breakdown,
            consensus_analysis=consensus_analysis,
            decision_threshold=0.75,
            require_consensus=False
        )
        
        assert recommendation == "no_hire"
        assert 0.0 <= confidence <= 1.0
    
    def test_assess_interviewer_consensus_unanimous(self, agent):
        """Test consensus assessment with unanimous agreement"""
        feedback = [
            {"recommendation": "strong_yes"},
            {"recommendation": "strong_yes"},
            {"recommendation": "strong_yes"}
        ]
        
        consensus = agent._assess_interviewer_consensus(feedback)
        
        assert consensus["unanimous"] is True
        assert consensus["majority"] is True
        assert consensus["split_decision"] is False
        assert consensus["strong_yes"] == 3
        assert consensus["total_interviewers"] == 3
    
    def test_assess_interviewer_consensus_split(self, agent):
        """Test consensus assessment with split decision"""
        feedback = [
            {"recommendation": "strong_yes"},
            {"recommendation": "no"},
            {"recommendation": "maybe"}
        ]
        
        consensus = agent._assess_interviewer_consensus(feedback)
        
        assert consensus["unanimous"] is False
        assert consensus["split_decision"] is True
        assert consensus["total_interviewers"] == 3
    
    def test_assess_interviewer_consensus_empty(self, agent):
        """Test consensus assessment with no feedback"""
        consensus = agent._assess_interviewer_consensus([])
        
        assert consensus["unanimous"] is False
        assert consensus["split_decision"] is True
        assert consensus["total_interviewers"] == 0
    
    def test_extract_strengths_and_concerns(self, agent):
        """Test extraction of strengths and concerns"""
        candidate = {
            "candidate_id": "C001",
            "screening_score": 0.87,
            "sourcing_notes": "Strong React background"
        }
        
        score_breakdown = {
            "technical_skills": 0.92,
            "problem_solving": 0.85,
            "communication": 0.95,
            "cultural_fit": 0.75,
            "leadership_potential": 0.55
        }
        
        transcript_insights = {
            "positive_indicators": ["Asked clarifying questions", "Explained thought process"],
            "concerns": []
        }
        
        consensus_analysis = {
            "unanimous": True
        }
        
        strengths, concerns = agent._extract_strengths_and_concerns(
            candidate,
            score_breakdown,
            transcript_insights,
            consensus_analysis
        )
        
        assert isinstance(strengths, list)
        assert isinstance(concerns, list)
        assert len(strengths) > 0
        assert any("Technical Skills" in s for s in strengths)
        assert any("Communication" in s for s in strengths)
    
    def test_generate_evaluation_summary(self, agent):
        """Test evaluation summary generation"""
        evaluated_candidates = [
            {"overall_score": 0.88, "recommendation": "strong_hire", "interviewer_consensus": {"unanimous": True}},
            {"overall_score": 0.76, "recommendation": "hire", "interviewer_consensus": {"majority": True}},
            {"overall_score": 0.68, "recommendation": "maybe", "interviewer_consensus": {"split_decision": True}},
            {"overall_score": 0.52, "recommendation": "no_hire", "interviewer_consensus": {"split_decision": True}}
        ]
        
        summary = agent._generate_evaluation_summary(evaluated_candidates)
        
        assert summary["strong_hire"] == 1
        assert summary["hire"] == 1
        assert summary["maybe"] == 1
        assert summary["no_hire"] == 1
        assert 0.0 <= summary["average_score"] <= 1.0
        assert summary["top_score"] == 0.88
        assert 0.0 <= summary["consensus_rate"] <= 1.0
    
    def test_generate_next_steps(self, agent):
        """Test next steps generation"""
        top_candidates = [
            {
                "candidate_id": "C001",
                "name": "Alice Johnson",
                "rank": 1,
                "recommendation": "strong_hire"
            },
            {
                "candidate_id": "C002",
                "name": "Bob Smith",
                "rank": 2,
                "recommendation": "hire"
            }
        ]
        
        next_steps = agent._generate_next_steps(top_candidates)
        
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        assert any("Alice Johnson" in step for step in next_steps)
        assert any("Bob Smith" in step for step in next_steps)
    
    @patch('agents.evaluation_agent.save_to_dynamodb')
    def test_evaluate_candidates_integration(self, mock_save, agent, sample_candidate_with_feedback):
        """Test full evaluate_candidates workflow"""
        result = agent.evaluate_candidates(
            job_id="test_job_001",
            candidates=[sample_candidate_with_feedback],
            evaluation_parameters={"decision_threshold": 0.75, "top_n_recommendations": 3}
        )
        
        assert result["status"] == "success"
        assert result["candidates_evaluated"] == 1
        assert len(result["recommendations"]) > 0
        assert "evaluation_summary" in result
        assert "next_steps" in result
        
        # Check recommendation structure
        rec = result["recommendations"][0]
        assert "candidate_id" in rec
        assert "overall_score" in rec
        assert "recommendation" in rec
        assert "confidence" in rec
        assert "score_breakdown" in rec
        assert "key_strengths" in rec
        assert "potential_concerns" in rec
    
    @patch('agents.evaluation_agent.save_to_dynamodb')
    def test_evaluate_candidates_empty_list(self, mock_save, agent):
        """Test evaluate_candidates with empty candidate list"""
        result = agent.evaluate_candidates(
            job_id="test_job_001",
            candidates=[],
            evaluation_parameters={}
        )
        
        assert result["status"] == "success"
        assert result["candidates_evaluated"] == 0
        assert len(result["recommendations"]) == 0
    
    def test_lambda_handler_success(self):
        """Test Lambda handler with valid event"""
        from agents.evaluation_agent import lambda_handler
        
        event = {
            "operation": "evaluate_candidates",
            "job_id": "test_job_001",
            "candidates": [
                {
                    "candidate_id": "C001",
                    "name": "Test Candidate",
                    "screening_score": 0.80,
                    "interviewer_feedback": [
                        {
                            "scores": {
                                "technical_skills": 4.0,
                                "problem_solving": 4.0,
                                "communication": 4.0,
                                "cultural_fit": 4.0,
                                "leadership_potential": 4.0
                            },
                            "recommendation": "yes"
                        }
                    ]
                }
            ],
            "evaluation_parameters": {"decision_threshold": 0.75}
        }
        
        with patch('agents.evaluation_agent.save_to_dynamodb'):
            response = lambda_handler(event, None)
        
        assert response["status"] == "success"
        assert "data" in response
    
    def test_lambda_handler_unknown_operation(self):
        """Test Lambda handler with unknown operation"""
        from agents.evaluation_agent import lambda_handler
        
        event = {
            "operation": "unknown_operation"
        }
        
        response = lambda_handler(event, None)
        
        assert response["status"] == "error"
        assert "Unknown operation" in response["error"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.evaluation_agent", "--cov-report=term-missing"])
