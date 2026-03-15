"""
Performance and Cost Validation Tests

Tests performance metrics, cost tracking, and resource usage.
Ensures system meets hackathon budget and performance targets.

Reference: 17_testing_strategy.md - Performance Testing
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from agents.supervisor_agent import SupervisorAgent


class TestPerformanceValidation:
    """Validate performance metrics and targets"""
    
    @pytest.fixture
    def supervisor(self):
        return SupervisorAgent()
    
    @pytest.fixture
    def standard_job(self):
        return {
            "job_id": "PERF-001",
            "title": "Software Engineer",
            "required_skills": ["Python", "Django"],
            "experience_years": 3
        }
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_latency_targets(self, supervisor, standard_job):
        """Test that pipeline meets latency targets"""
        
        start_time = time.time()
        result = await supervisor.run_recruiting_pipeline(standard_job)
        execution_time = time.time() - start_time
        
        assert result["status"] == "completed"
        
        # Overall pipeline: < 60 seconds
        assert execution_time < 60, f"Pipeline took {execution_time:.2f}s (target: < 60s)"
        
        # Individual stage targets
        stages = result["stages"]
        assert stages["sourcing"]["duration"] < 15, "Sourcing too slow"
        assert stages["screening"]["duration"] < 20, "Screening too slow"
        assert stages["outreach"]["duration"] < 10, "Outreach too slow"
        
        print(f"\n✅ Latency Targets - PASSED")
        print(f"   Total: {execution_time:.2f}s (target: < 60s)")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cost_budget(self, supervisor, standard_job):
        """Test that costs stay within AWS credits budget"""
        
        result = await supervisor.run_recruiting_pipeline(standard_job)
        
        assert result["status"] == "completed"
        
        total_cost = result["total_cost"]
        
        # Per-job cost: < $0.50
        assert total_cost < 0.50, f"Cost ${total_cost:.4f} exceeds target ($0.50)"
        
        # Token usage reasonable
        tokens = result["token_usage"]["total_tokens"]
        assert tokens < 100000, f"Token usage {tokens:,} too high"
        
        print(f"\n✅ Cost Budget - PASSED")
        print(f"   Cost: ${total_cost:.4f} (target: < $0.50)")
        print(f"   Tokens: {tokens:,}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
