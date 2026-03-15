"""
Demo Scenario Tests for Talent Acquisition Accelerator

Tests specific demo scenarios that will be shown in the hackathon video.
Ensures all demo paths work 100% reliably.

Reference: 19_demo_data_preparation.md - Demo Scenarios
"""

import pytest
import asyncio
import json
from typing import Dict, Any

from agents.supervisor_agent import SupervisorAgent
from shared.utils import load_demo_data


class TestDemoScenarios:
    """Test scenarios specifically for demo video"""
    
    @pytest.fixture
    def supervisor(self):
        """Initialize supervisor agent"""
        return SupervisorAgent()
    
    @pytest.fixture
    def demo_jobs(self):
        """Load demo job descriptions"""
        return {
            "senior_swe": {
                "job_id": "DEMO-JOB-001",
                "title": "Senior Software Engineer - Frontend",
                "company": "TechCorp",
                "location": "Seattle, WA or Remote (US)",
                "required_skills": ["React", "TypeScript", "JavaScript", "Node.js", "GraphQL"],
                "preferred_skills": ["AWS", "Next.js", "Redux"],
                "experience_years": 5,
                "description": "Lead frontend development for customer-facing products serving 2M+ users."
            },
            "product_manager": {
                "job_id": "DEMO-JOB-002",
                "title": "Senior Product Manager - B2B SaaS",
                "company": "TechCorp",
                "location": "San Francisco, CA (Hybrid)",
                "required_skills": ["Product Management", "B2B SaaS", "Analytics", "Stakeholder Management"],
                "experience_years": 5,
                "description": "Lead product strategy for enterprise SaaS platform."
            },
            "data_scientist": {
                "job_id": "DEMO-JOB-003",
                "title": "Senior Data Scientist - Machine Learning",
                "company": "TechCorp",
                "location": "Remote (US)",
                "required_skills": ["Python", "Machine Learning", "SQL", "Statistics"],
                "preferred_skills": ["Deep Learning", "MLOps", "Spark"],
                "experience_years": 4,
                "description": "Build ML models for recommendation engine serving millions of predictions daily."
            }
        }
    
    @pytest.mark.asyncio
    @pytest.mark.demo
    async def test_demo_scenario_1_happy_path(self, supervisor, demo_jobs):
        """
        Demo Scenario 1: Complete recruiting workflow (Happy Path)
        
        This is the primary demo scenario showing all 5 agents in action.
        Must work 100% reliably for video recording.
        """
        job = demo_jobs["senior_swe"]
        
        result = await supervisor.run_recruiting_pipeline(job)
        
        # Critical assertions for demo
        assert result["status"] == "completed", "Demo scenario MUST complete successfully"
        
        # Validate each stage for demo
        stages = result["stages"]
        
        # Sourcing: Should find 20-50 candidates
        assert stages["sourcing"]["candidates_found"] >= 20
        assert stages["sourcing"]["candidates_found"] <= 50
        
        # Screening: Should qualify 30-50% of candidates
        qualified_count = stages["screening"]["qualified_candidates"]
        sourced_count = stages["sourcing"]["candidates_found"]
        qualification_rate = qualified_count / sourced_count
        assert 0.30 <= qualification_rate <= 0.50, f"Qualification rate {qualification_rate:.2%} outside demo range"
        
        # Outreach: Should send messages to top candidates
        assert stages["outreach"]["messages_sent"] >= 5
        assert stages["outreach"]["messages_sent"] <= 15
        
        # Scheduling: Should schedule some interviews
        assert stages["scheduling"]["interviews_scheduled"] >= 3
        
        # Evaluation: Should have top 3-5 candidates
        top_candidates = stages["evaluation"]["top_candidates"]
        assert 3 <= len(top_candidates) <= 5
        
        # Validate top candidate has all required fields for demo
        top_candidate = top_candidates[0]
        required_fields = ["candidate_id", "name", "overall_score", "recommendation", "reasoning"]
        for field in required_fields:
            assert field in top_candidate, f"Missing {field} in top candidate"
        
        # Score should be impressive for demo
        assert top_candidate["overall_score"] >= 0.80, "Top candidate score should be 80%+ for demo"
        
        print(f"\n✅ DEMO SCENARIO 1 (Happy Path) - READY FOR VIDEO")
        print(f"   📊 Sourced: {sourced_count} candidates")
        print(f"   ✓ Qualified: {qualified_count} candidates ({qualification_rate:.1%})")
        print(f"   📧 Outreach: {stages['outreach']['messages_sent']} messages")
        print(f"   📅 Scheduled: {stages['scheduling']['interviews_scheduled']} interviews")
        print(f"   🏆 Top Candidate: {top_candidate['name']} (Score: {top_candidate['overall_score']:.2%})")
    
    @pytest.mark.asyncio
    @pytest.mark.demo
    async def test_demo_scenario_2_high_volume(self, supervisor, demo_jobs):
        """
        Demo Scenario 2: High-volume sourcing
        
        Demonstrates system can handle large candidate pools efficiently.
        Shows scalability for enterprise use cases.
        """
        job = demo_jobs["data_scientist"]
        
        # Configure for high volume
        job["target_candidates"] = 100
        
        result = await supervisor.run_recruiting_pipeline(job)
        
        assert result["status"] == "completed"
        
        # Should handle 100+ candidates
        sourced = result["stages"]["sourcing"]["candidates_found"]
        assert sourced >= 80, f"High-volume demo should source 80+ candidates, got {sourced}"
        
        # Should still complete in reasonable time
        execution_time = result.get("execution_time", 0)
        assert execution_time < 60, f"High-volume demo took {execution_time}s (should be < 60s)"
        
        print(f"\n✅ DEMO SCENARIO 2 (High Volume) - READY FOR VIDEO")
        print(f"   📊 Sourced: {sourced} candidates")
        print(f"   ⚡ Time: {execution_time:.1f}s")
        print(f"   💰 Cost: ${result.get('total_cost', 0):.4f}")
    
    @pytest.mark.asyncio
    @pytest.mark.demo
    async def test_demo_scenario_3_edge_cases(self, supervisor):
        """
        Demo Scenario 3: Intelligent edge case handling
        
        Shows system handles non-standard candidates intelligently.
        Demonstrates AI reasoning capabilities.
        """
        
        # Job with specific requirements
        job = {
            "job_id": "DEMO-JOB-EDGE",
            "title": "Senior Software Engineer",
            "required_skills": ["React", "TypeScript"],
            "experience_years": 5
        }
        
        # Inject edge case candidates
        edge_candidates = [
            {
                "candidate_id": "EDGE-001",
                "name": "Morgan Lee",
                "skills": ["React", "TypeScript", "Node.js", "AWS"],
                "experience_years": 12,
                "note": "Over-qualified - Staff level at FAANG"
            },
            {
                "candidate_id": "EDGE-002",
                "name": "Casey Brown",
                "skills": ["React", "TypeScript", "GraphQL"],
                "experience_years": 7,
                "employment_gap": "1 year (2023-2024) - Family caregiving"
            },
            {
                "candidate_id": "EDGE-003",
                "name": "Riley Johnson",
                "skills": ["Vue.js", "JavaScript", "Python"],
                "experience_years": 6,
                "note": "Wrong framework - Vue instead of React"
            }
        ]
        
        # Run screening on edge cases
        from agents.screening_agent import ScreeningAgent
        screening = ScreeningAgent()
        
        result = await screening.screen_candidates(
            candidates=edge_candidates,
            job=job
        )
        
        assert result["status"] == "completed"
        
        # Validate intelligent handling
        screened = result["screened_candidates"]
        
        # Over-qualified candidate should pass with flag
        morgan = next(c for c in screened if c["candidate_id"] == "EDGE-001")
        assert morgan["qualified"] == True
        assert "over-qualified" in morgan["notes"].lower() or "retention" in morgan["notes"].lower()
        
        # Career gap candidate should pass with note
        casey = next(c for c in screened if c["candidate_id"] == "EDGE-002")
        assert casey["qualified"] == True
        assert "gap" in casey["notes"].lower()
        
        # Skills mismatch should fail
        riley = next(c for c in screened if c["candidate_id"] == "EDGE-003")
        assert riley["qualified"] == False
        assert "react" in riley["notes"].lower()
        
        print(f"\n✅ DEMO SCENARIO 3 (Edge Cases) - READY FOR VIDEO")
        print(f"   ✓ Over-qualified: Flagged appropriately")
        print(f"   ✓ Career gap: Noted for discussion")
        print(f"   ✗ Skills mismatch: Correctly rejected")
    
    @pytest.mark.asyncio
    @pytest.mark.demo
    async def test_demo_consistency_check(self, supervisor, demo_jobs):
        """
        Run all demo scenarios 5 times to ensure consistency
        
        Demo scenarios MUST work reliably for video recording.
        This test validates 100% success rate.
        """
        job = demo_jobs["senior_swe"]
        
        success_count = 0
        num_runs = 5
        
        for i in range(num_runs):
            result = await supervisor.run_recruiting_pipeline(job)
            if result["status"] == "completed":
                success_count += 1
        
        success_rate = success_count / num_runs
        
        assert success_rate == 1.0, f"Demo consistency check failed: {success_rate:.1%} success rate (need 100%)"
        
        print(f"\n✅ DEMO CONSISTENCY CHECK - PASSED")
        print(f"   ✓ {success_count}/{num_runs} runs successful (100%)")
        print(f"   🎬 Ready for video recording!")


class TestDemoDataQuality:
    """Test quality of demo data and outputs"""
    
    @pytest.mark.asyncio
    @pytest.mark.demo
    async def test_outreach_message_quality(self):
        """Test that outreach messages are demo-worthy"""
        
        from agents.outreach_agent import OutreachAgent
        
        outreach = OutreachAgent()
        
        candidate = {
            "candidate_id": "DEMO-C001",
            "name": "Alex Chen",
            "email": "alex@example.com",
            "skills": ["React", "TypeScript", "AWS"],
            "experience_years": 7,
            "current_role": "Senior Software Engineer at CloudTech"
        }
        
        job = {
            "job_id": "DEMO-JOB-001",
            "title": "Senior Software Engineer",
            "company": "TechCorp"
        }
        
        result = await outreach.generate_message(candidate, job)
        
        message = result["message"]
        
        # Quality checks for demo
        assert len(message["subject"]) > 10, "Subject line too short"
        assert len(message["body"]) > 100, "Message body too short"
        assert candidate["name"] in message["body"], "Message not personalized"
        assert job["company"] in message["body"], "Company not mentioned"
        
        # Check for professional tone
        assert not any(word in message["body"].lower() for word in ["hey", "yo", "sup"]), "Tone too casual"
        
        print(f"\n✅ Outreach Message Quality - DEMO READY")
        print(f"   Subject: {message['subject']}")
        print(f"   Length: {len(message['body'])} characters")
    
    @pytest.mark.asyncio
    @pytest.mark.demo
    async def test_evaluation_report_quality(self):
        """Test that evaluation reports are comprehensive and demo-worthy"""
        
        from agents.evaluation_agent import EvaluationAgent
        
        evaluation = EvaluationAgent()
        
        # Mock candidate with full pipeline data
        candidate_data = {
            "candidate_id": "DEMO-C001",
            "name": "Alex Chen",
            "sourcing_score": 0.92,
            "screening_score": 0.87,
            "interview_feedback": "Strong technical skills, good culture fit",
            "skills_match": 0.90
        }
        
        result = await evaluation.generate_report(candidate_data)
        
        report = result["report"]
        
        # Quality checks for demo
        assert "overall_score" in report
        assert "recommendation" in report
        assert "reasoning" in report
        assert len(report["reasoning"]) > 50, "Reasoning too brief"
        
        # Should synthesize multiple data points
        assert "sourcing" in report["reasoning"].lower() or "screening" in report["reasoning"].lower()
        
        print(f"\n✅ Evaluation Report Quality - DEMO READY")
        print(f"   Overall Score: {report['overall_score']:.2%}")
        print(f"   Recommendation: {report['recommendation']}")


if __name__ == "__main__":
    # Run demo tests
    pytest.main([__file__, "-v", "-m", "demo"])
