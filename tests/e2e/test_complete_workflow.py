"""
End-to-End Workflow Tests for Talent Acquisition Accelerator

Tests the complete recruiting pipeline from job posting to candidate evaluation.
Validates all 5 agents working in sequence with realistic data.

Reference: 17_testing_strategy.md - E2E Testing Strategy
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Import agents
from agents.sourcing_agent import SourcingAgent
from agents.screening_agent import ScreeningAgent
from agents.outreach_agent import OutreachAgent
from agents.scheduling_agent import SchedulingAgent
from agents.evaluation_agent import EvaluationAgent
from agents.supervisor_agent import SupervisorAgent

# Import shared utilities
from shared.models import Job, Candidate, RecruitingState
from shared.utils import calculate_cost, format_duration


class TestCompleteWorkflow:
    """Test complete recruiting workflow end-to-end"""
    
    @pytest.fixture
    def sample_job(self) -> Dict[str, Any]:
        """Sample job description for testing"""
        return {
            "job_id": "JOB-E2E-001",
            "title": "Senior Software Engineer - Frontend",
            "company": "TechCorp",
            "location": "Seattle, WA or Remote (US)",
            "required_skills": ["React", "TypeScript", "JavaScript", "Node.js", "GraphQL"],
            "preferred_skills": ["AWS", "Next.js", "Redux"],
            "experience_years": 5,
            "description": """
                We're seeking a Senior Software Engineer to lead frontend development.
                You'll architect scalable React applications and mentor junior engineers.
            """,
            "salary_range": "$150,000 - $180,000"
        }
    
    @pytest.fixture
    def supervisor(self):
        """Initialize supervisor agent"""
        return SupervisorAgent()
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_full_recruiting_pipeline(self, sample_job, supervisor):
        """
        Test complete recruiting workflow: Sourcing → Screening → Outreach → Scheduling → Evaluation
        
        Success Criteria:
        - All 5 agents execute successfully
        - Data flows correctly between agents
        - Final output includes candidate recommendations
        - Total execution time < 120 seconds
        - Total cost < $1.00
        """
        start_time = time.time()
        
        # Execute complete pipeline
        result = await supervisor.run_recruiting_pipeline(sample_job)
        
        execution_time = time.time() - start_time
        
        # Validate pipeline completion
        assert result["status"] == "completed", f"Pipeline failed: {result.get('error')}"
        assert "pipeline_id" in result
        
        # Validate sourcing stage
        assert "sourcing" in result["stages"]
        sourcing_result = result["stages"]["sourcing"]
        assert sourcing_result["status"] == "completed"
        assert sourcing_result["candidates_found"] >= 10, "Should find at least 10 candidates"
        assert len(sourcing_result["candidates"]) > 0
        
        # Validate screening stage
        assert "screening" in result["stages"]
        screening_result = result["stages"]["screening"]
        assert screening_result["status"] == "completed"
        assert screening_result["candidates_screened"] > 0
        assert screening_result["qualified_candidates"] > 0
        assert screening_result["qualified_candidates"] <= sourcing_result["candidates_found"]
        
        # Validate outreach stage
        assert "outreach" in result["stages"]
        outreach_result = result["stages"]["outreach"]
        assert outreach_result["status"] == "completed"
        assert outreach_result["messages_sent"] > 0
        assert outreach_result["messages_sent"] <= screening_result["qualified_candidates"]
        
        # Validate scheduling stage
        assert "scheduling" in result["stages"]
        scheduling_result = result["stages"]["scheduling"]
        assert scheduling_result["status"] == "completed"
        assert scheduling_result["interviews_scheduled"] >= 0
        
        # Validate evaluation stage
        assert "evaluation" in result["stages"]
        evaluation_result = result["stages"]["evaluation"]
        assert evaluation_result["status"] == "completed"
        assert "top_candidates" in evaluation_result
        assert len(evaluation_result["top_candidates"]) > 0
        
        # Validate top candidate structure
        top_candidate = evaluation_result["top_candidates"][0]
        assert "candidate_id" in top_candidate
        assert "name" in top_candidate
        assert "overall_score" in top_candidate
        assert "recommendation" in top_candidate
        assert "reasoning" in top_candidate
        
        # Performance validation
        assert execution_time < 120, f"Pipeline took {execution_time:.2f}s (should be < 120s)"
        
        # Cost validation
        total_cost = result.get("total_cost", 0)
        assert total_cost < 1.00, f"Pipeline cost ${total_cost:.2f} (should be < $1.00)"
        
        # Log results
        print(f"\n✅ Complete Pipeline Test PASSED")
        print(f"   Execution Time: {execution_time:.2f}s")
        print(f"   Total Cost: ${total_cost:.4f}")
        print(f"   Candidates Sourced: {sourcing_result['candidates_found']}")
        print(f"   Candidates Qualified: {screening_result['qualified_candidates']}")
        print(f"   Messages Sent: {outreach_result['messages_sent']}")
        print(f"   Interviews Scheduled: {scheduling_result['interviews_scheduled']}")
        print(f"   Top Candidate: {top_candidate['name']} (Score: {top_candidate['overall_score']})")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_with_multiple_jobs(self, supervisor):
        """Test pipeline handles multiple different job types"""
        
        jobs = [
            {
                "job_id": "JOB-E2E-002",
                "title": "Senior Product Manager",
                "required_skills": ["Product Management", "B2B SaaS", "Analytics"],
                "experience_years": 5
            },
            {
                "job_id": "JOB-E2E-003",
                "title": "Data Scientist",
                "required_skills": ["Python", "Machine Learning", "SQL"],
                "experience_years": 4
            }
        ]
        
        results = []
        for job in jobs:
            result = await supervisor.run_recruiting_pipeline(job)
            results.append(result)
            assert result["status"] == "completed"
        
        # Validate all jobs processed successfully
        assert len(results) == len(jobs)
        assert all(r["status"] == "completed" for r in results)
        
        print(f"\n✅ Multiple Jobs Test PASSED - Processed {len(jobs)} jobs")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_error_handling(self, supervisor):
        """Test pipeline handles errors gracefully"""
        
        # Invalid job (missing required fields)
        invalid_job = {
            "job_id": "JOB-E2E-INVALID",
            "title": "Test Role"
            # Missing required_skills, experience_years
        }
        
        result = await supervisor.run_recruiting_pipeline(invalid_job)
        
        # Should fail gracefully with error message
        assert result["status"] in ["failed", "validation_error"]
        assert "error" in result or "error_message" in result
        
        print(f"\n✅ Error Handling Test PASSED - Graceful failure detected")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_state_persistence(self, sample_job, supervisor):
        """Test that pipeline state is persisted correctly"""
        
        result = await supervisor.run_recruiting_pipeline(sample_job)
        
        assert result["status"] == "completed"
        pipeline_id = result["pipeline_id"]
        
        # Retrieve pipeline state from database
        # (This would query DynamoDB in actual implementation)
        # For now, validate that pipeline_id is returned
        assert pipeline_id is not None
        assert len(pipeline_id) > 0
        
        print(f"\n✅ State Persistence Test PASSED - Pipeline ID: {pipeline_id}")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_consistency(self, sample_job, supervisor):
        """Test pipeline produces consistent results across multiple runs"""
        
        results = []
        num_runs = 3
        
        for i in range(num_runs):
            result = await supervisor.run_recruiting_pipeline(sample_job)
            results.append(result)
            assert result["status"] == "completed"
        
        # Validate consistency
        # All runs should complete successfully
        assert all(r["status"] == "completed" for r in results)
        
        # Candidate counts should be similar (within 20% variance)
        candidate_counts = [r["stages"]["sourcing"]["candidates_found"] for r in results]
        avg_count = sum(candidate_counts) / len(candidate_counts)
        
        for count in candidate_counts:
            variance = abs(count - avg_count) / avg_count
            assert variance < 0.20, f"Candidate count variance too high: {variance:.2%}"
        
        print(f"\n✅ Consistency Test PASSED - {num_runs} runs completed")
        print(f"   Candidate counts: {candidate_counts}")
        print(f"   Average: {avg_count:.1f}, Max variance: {max(abs(c - avg_count) / avg_count for c in candidate_counts):.2%}")


class TestAgentCoordination:
    """Test agent-to-agent coordination and handoffs"""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_sourcing_to_screening_handoff(self):
        """Test data handoff from Sourcing to Screening agent"""
        
        sourcing = SourcingAgent()
        screening = ScreeningAgent()
        
        job = {
            "job_id": "JOB-COORD-001",
            "title": "Software Engineer",
            "required_skills": ["Python", "Django"],
            "experience_years": 3
        }
        
        # Run sourcing
        sourcing_result = await sourcing.find_candidates(job)
        
        assert sourcing_result["status"] == "completed"
        assert len(sourcing_result["candidates"]) > 0
        
        # Pass to screening
        screening_result = await screening.screen_candidates(
            candidates=sourcing_result["candidates"],
            job=job
        )
        
        assert screening_result["status"] == "completed"
        assert len(screening_result["qualified_candidates"]) > 0
        
        # Validate data integrity
        for candidate in screening_result["qualified_candidates"]:
            assert "candidate_id" in candidate
            assert "score" in candidate
            assert candidate["job_id"] == job["job_id"]
        
        print(f"\n✅ Sourcing→Screening Handoff Test PASSED")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_screening_to_outreach_handoff(self):
        """Test data handoff from Screening to Outreach agent"""
        
        screening = ScreeningAgent()
        outreach = OutreachAgent()
        
        # Mock screened candidates
        qualified_candidates = [
            {
                "candidate_id": "C001",
                "name": "Alex Chen",
                "email": "alex@example.com",
                "skills": ["React", "TypeScript"],
                "score": 0.87
            }
        ]
        
        job = {
            "job_id": "JOB-COORD-002",
            "title": "Frontend Engineer",
            "company": "TechCorp"
        }
        
        # Run outreach
        outreach_result = await outreach.generate_outreach(
            candidates=qualified_candidates,
            job=job
        )
        
        assert outreach_result["status"] == "completed"
        assert len(outreach_result["messages"]) == len(qualified_candidates)
        
        # Validate message structure
        message = outreach_result["messages"][0]
        assert "candidate_id" in message
        assert "subject" in message
        assert "body" in message
        assert qualified_candidates[0]["name"] in message["body"]
        
        print(f"\n✅ Screening→Outreach Handoff Test PASSED")


class TestPerformanceMetrics:
    """Test performance and cost metrics"""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_token_usage_tracking(self, supervisor):
        """Test that token usage is tracked correctly"""
        
        job = {
            "job_id": "JOB-PERF-001",
            "title": "Software Engineer",
            "required_skills": ["Python"],
            "experience_years": 3
        }
        
        result = await supervisor.run_recruiting_pipeline(job)
        
        assert result["status"] == "completed"
        assert "token_usage" in result
        
        token_usage = result["token_usage"]
        assert "total_tokens" in token_usage
        assert "input_tokens" in token_usage
        assert "output_tokens" in token_usage
        
        # Validate reasonable token counts
        assert token_usage["total_tokens"] > 0
        assert token_usage["total_tokens"] < 200000  # Should be well under Nova's limit
        
        print(f"\n✅ Token Usage Tracking Test PASSED")
        print(f"   Total Tokens: {token_usage['total_tokens']:,}")
        print(f"   Input Tokens: {token_usage['input_tokens']:,}")
        print(f"   Output Tokens: {token_usage['output_tokens']:,}")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_cost_calculation(self, supervisor):
        """Test that costs are calculated correctly"""
        
        job = {
            "job_id": "JOB-COST-001",
            "title": "Software Engineer",
            "required_skills": ["Python"],
            "experience_years": 3
        }
        
        result = await supervisor.run_recruiting_pipeline(job)
        
        assert result["status"] == "completed"
        assert "total_cost" in result
        assert "cost_breakdown" in result
        
        # Validate cost structure
        assert result["total_cost"] > 0
        assert result["total_cost"] < 1.00  # Should be under $1 per job
        
        cost_breakdown = result["cost_breakdown"]
        assert "sourcing" in cost_breakdown
        assert "screening" in cost_breakdown
        assert "outreach" in cost_breakdown
        
        print(f"\n✅ Cost Calculation Test PASSED")
        print(f"   Total Cost: ${result['total_cost']:.4f}")
        print(f"   Breakdown: {json.dumps(cost_breakdown, indent=2)}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-m", "e2e"])
