"""
Integration test for Evaluation Agent

This script demonstrates the Evaluation Agent working with realistic data.
Run: python -m pytest tests/test_evaluation_integration.py -v -s
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.evaluation_agent import EvaluationAgent


def test_evaluation_agent_realistic_scenario():
    """Test Evaluation Agent with realistic interview scenario"""
    
    print("\n" + "="*80)
    print("EVALUATION AGENT - REALISTIC SCENARIO TEST")
    print("="*80)
    
    agent = EvaluationAgent()
    
    # Realistic candidate data with interview feedback
    candidates = [
        {
            "candidate_id": "C001",
            "name": "Alice Johnson",
            "screening_score": 0.87,
            "sourcing_notes": "7 years React experience, AWS certified Solutions Architect",
            "interview_data": {
                "interview_id": "INT001",
                "interview_type": "technical_screen",
                "interview_date": "2026-03-18T14:00:00Z",
                "duration_minutes": 60
            },
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
                    "comments": "Strong technical skills, excellent communication. Solved coding challenge efficiently with clean code.",
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
                    "comments": "Excellent problem-solving approach. Asked great clarifying questions.",
                    "recommendation": "strong_yes",
                    "confidence": 0.85
                }
            ]
        },
        {
            "candidate_id": "C002",
            "name": "Bob Smith",
            "screening_score": 0.75,
            "sourcing_notes": "5 years backend experience with Python and Node.js",
            "interview_data": {
                "interview_id": "INT002",
                "interview_type": "technical_screen",
                "interview_date": "2026-03-18T15:00:00Z",
                "duration_minutes": 60
            },
            "interviewer_feedback": [
                {
                    "interviewer_name": "Jane Smith",
                    "interviewer_role": "Senior Engineer",
                    "scores": {
                        "technical_skills": 4.0,
                        "problem_solving": 3.5,
                        "communication": 4.0,
                        "cultural_fit": 4.0,
                        "leadership_potential": 3.5
                    },
                    "comments": "Solid technical skills, good problem-solving approach. Could improve on system design thinking.",
                    "recommendation": "yes",
                    "confidence": 0.8
                }
            ]
        },
        {
            "candidate_id": "C003",
            "name": "Carol Williams",
            "screening_score": 0.82,
            "sourcing_notes": "8 years full-stack experience, team lead at previous company",
            "interview_data": {
                "interview_id": "INT003",
                "interview_type": "technical_screen",
                "interview_date": "2026-03-18T16:00:00Z",
                "duration_minutes": 60
            },
            "interviewer_feedback": [
                {
                    "interviewer_name": "Jane Smith",
                    "interviewer_role": "Senior Engineer",
                    "scores": {
                        "technical_skills": 3.5,
                        "problem_solving": 4.0,
                        "communication": 4.5,
                        "cultural_fit": 4.5,
                        "leadership_potential": 5.0
                    },
                    "comments": "Strong leadership potential and communication. Technical skills adequate but not exceptional.",
                    "recommendation": "yes",
                    "confidence": 0.75
                },
                {
                    "interviewer_name": "John Doe",
                    "interviewer_role": "Tech Lead",
                    "scores": {
                        "technical_skills": 3.0,
                        "problem_solving": 3.5,
                        "communication": 4.0,
                        "cultural_fit": 4.0,
                        "leadership_potential": 4.5
                    },
                    "comments": "Good leadership experience but struggled with advanced technical questions.",
                    "recommendation": "maybe",
                    "confidence": 0.65
                }
            ]
        }
    ]
    
    # Run evaluation
    result = agent.evaluate_candidates(
        job_id="job_senior_engineer_001",
        candidates=candidates,
        evaluation_parameters={
            "decision_threshold": 0.75,
            "top_n_recommendations": 3,
            "require_consensus": False
        }
    )
    
    # Display results
    print(f"\nStatus: {result['status']}")
    print(f"Candidates Evaluated: {result['candidates_evaluated']}")
    print(f"\nConfidence: {result['confidence']}")
    print(f"Reasoning: {result['reasoning']}")
    
    print("\n" + "-"*80)
    print("TOP RECOMMENDATIONS")
    print("-"*80)
    
    for rec in result['recommendations']:
        print(f"\nRank #{rec['rank']}: {rec['name']} (ID: {rec['candidate_id']})")
        print(f"  Overall Score: {rec['overall_score']}")
        print(f"  Recommendation: {rec['recommendation'].upper()}")
        print(f"  Confidence: {rec['confidence']}")
        
        print(f"\n  Score Breakdown:")
        for category, score in rec['score_breakdown'].items():
            print(f"    - {category.replace('_', ' ').title()}: {score}")
        
        print(f"\n  Key Strengths:")
        for strength in rec['key_strengths']:
            print(f"    ✓ {strength}")
        
        if rec['potential_concerns']:
            print(f"\n  Potential Concerns:")
            for concern in rec['potential_concerns']:
                print(f"    ⚠ {concern}")
        
        print(f"\n  Interviewer Consensus:")
        consensus = rec['interviewer_consensus']
        print(f"    - Unanimous: {consensus['unanimous']}")
        print(f"    - Strong Yes: {consensus['strong_yes']}, Yes: {consensus['yes']}, "
              f"Maybe: {consensus['maybe']}, No: {consensus['no']}")
        
        print(f"\n  Hiring Recommendation:")
        print(f"    {rec['hiring_recommendation']}")
    
    print("\n" + "-"*80)
    print("EVALUATION SUMMARY")
    print("-"*80)
    
    summary = result['evaluation_summary']
    print(f"  Strong Hire: {summary['strong_hire']}")
    print(f"  Hire: {summary['hire']}")
    print(f"  Maybe: {summary['maybe']}")
    print(f"  No Hire: {summary['no_hire']}")
    print(f"  Average Score: {summary['average_score']}")
    print(f"  Top Score: {summary['top_score']}")
    print(f"  Consensus Rate: {summary['consensus_rate']}")
    
    print("\n" + "-"*80)
    print("NEXT STEPS")
    print("-"*80)
    
    for i, step in enumerate(result['next_steps'], 1):
        print(f"  {i}. {step}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")
    
    # Assertions for test validation
    assert result['status'] == 'success'
    assert result['candidates_evaluated'] == 3
    assert len(result['recommendations']) == 3
    assert result['recommendations'][0]['rank'] == 1
    assert result['recommendations'][0]['overall_score'] > result['recommendations'][1]['overall_score']
    
    print("✓ All assertions passed!")


if __name__ == "__main__":
    test_evaluation_agent_realistic_scenario()
