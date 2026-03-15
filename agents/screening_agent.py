"""
Screening Agent - Evaluates candidate qualifications and produces ranked shortlist

This module implements the Screening Agent, which analyzes candidates from the Sourcing Agent,
evaluates them against job requirements using a multi-dimensional scoring rubric, and produces
a ranked shortlist of qualified candidates.

References:
- Governing Doc: 00_governing_docs/08_agent_specifications.md (Section 5: Screening Agent)
- Architecture: 00_governing_docs/07_system_architecture.md
- Build Checklist: 00_governing_docs/16_module_build_checklist.md (Phase 4.2)

Verification Sources:
- Resume Parsing Guide: https://www.hiretual.com/blog/resume-parsing-guide
- Candidate Scoring: https://www.lever.co/blog/candidate-scoring-guide
- Bias Mitigation: https://www.shrm.org/topics-tools/news/talent-acquisition/how-to-reduce-bias-in-hiring
- AI Resume Screening: https://www.ongig.com/blog/ai-resume-screening/
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from shared.utils import (
    invoke_bedrock,
    get_from_dynamodb,
    save_to_dynamodb,
    Config,
    format_success_response,
    format_error_response,
    generate_id,
    get_timestamp
)
from shared.models import Candidate, Job

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ScreeningAgent:
    """
    Screening Agent evaluates candidates against job requirements
    
    Responsibilities:
    1. Resume analysis and parsing
    2. Multi-dimensional scoring (skills, experience, education, cultural fit)
    3. Pass/fail determination
    4. Candidate ranking and shortlist generation
    5. Bias mitigation through objective criteria
    
    Scoring Rubric (from 08_agent_specifications.md):
    - Required Skills: 35% (must-have match)
    - Experience: 25% (years in range)
    - Education: 15% (degree level)
    - Preferred Skills: 15% (nice-to-have)
    - Cultural Fit: 10% (indicators from resume)
    """
    
    def __init__(self):
        """Initialize Screening Agent"""
        self.agent_name = "ScreeningAgent"
        self.agent_role = "Candidate Qualification Evaluator"
        
        # Scoring weights from agent specifications
        self.score_weights = {
            "required_skills": 0.35,
            "experience": 0.25,
            "education": 0.15,
            "preferred_skills": 0.15,
            "cultural_fit": 0.10
        }
        
        logger.info(f"{self.agent_name} initialized with scoring weights: {self.score_weights}")
    
    def screen_candidates(
        self,
        job_id: str,
        job_requirements: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        screening_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Screen candidates and produce ranked shortlist
        
        Args:
            job_id: Job requisition ID
            job_requirements: Job requirements dict with required_skills, experience_years, etc.
            candidates: List of candidate dicts from Sourcing Agent
            screening_parameters: Optional parameters (pass_threshold, top_n, etc.)
        
        Returns:
            Dict with qualified candidates, rankings, and screening summary
        
        Example:
            >>> agent = ScreeningAgent()
            >>> result = agent.screen_candidates(
            ...     job_id="job_001",
            ...     job_requirements={"required_skills": ["Python", "AWS"], ...},
            ...     candidates=[{...}, {...}],
            ...     screening_parameters={"pass_threshold": 0.70, "top_n": 15}
            ... )
            >>> print(result["qualified_candidates"])
        """
        try:
            logger.info(f"Starting candidate screening for job {job_id} with {len(candidates)} candidates")
            
            # Set default parameters
            params = screening_parameters or {}
            pass_threshold = params.get("pass_threshold", 0.70)
            top_n = params.get("top_n", 15)
            require_all_must_haves = params.get("require_all_must_haves", True)
            
            # Screen each candidate
            screened_candidates = []
            disqualified_candidates = []
            
            for candidate in candidates:
                # Calculate comprehensive score
                overall_score, score_breakdown = self.calculate_screening_score(
                    candidate,
                    job_requirements
                )
                
                # Determine pass/fail
                passed, reason = self.should_pass_screening(
                    overall_score,
                    score_breakdown,
                    pass_threshold,
                    require_all_must_haves
                )
                
                # Extract strengths and concerns
                strengths, concerns = self._analyze_candidate_profile(
                    candidate,
                    job_requirements,
                    score_breakdown
                )
                
                candidate_result = {
                    "candidate_id": candidate.get("candidate_id"),
                    "name": candidate.get("name", "[Name]"),
                    "overall_score": round(overall_score, 2),
                    "score_breakdown": {k: round(v, 2) for k, v in score_breakdown.items()},
                    "strengths": strengths,
                    "concerns": concerns,
                    "passed": passed,
                    "disqualification_reason": reason if not passed else None
                }
                
                if passed:
                    screened_candidates.append(candidate_result)
                else:
                    disqualified_candidates.append(candidate_result)
            
            # Rank qualified candidates
            screened_candidates.sort(key=lambda x: x["overall_score"], reverse=True)
            
            # Add rank and recommendation
            for rank, candidate in enumerate(screened_candidates[:top_n], 1):
                candidate["rank"] = rank
                candidate["recommendation"] = self._generate_recommendation(
                    candidate["overall_score"],
                    candidate["score_breakdown"]
                )
                candidate["confidence"] = self._calculate_confidence(candidate["score_breakdown"])
            
            # Generate screening summary
            screening_summary = self._generate_screening_summary(
                screened_candidates,
                disqualified_candidates,
                job_requirements
            )
            
            # Save qualified candidates to DynamoDB
            self._save_screening_results(job_id, screened_candidates[:top_n])
            
            logger.info(f"Screening complete: {len(screened_candidates)} qualified, "
                       f"{len(disqualified_candidates)} disqualified")
            
            return {
                "status": "success",
                "candidates_screened": len(candidates),
                "qualified_candidates": len(screened_candidates),
                "top_candidates": screened_candidates[:top_n],
                "disqualified_candidates": disqualified_candidates,
                "screening_summary": screening_summary,
                "confidence": 0.85,
                "reasoning": f"{len(screened_candidates)} candidates meet minimum qualifications. "
                           f"Top {min(top_n, len(screened_candidates))} have strong skill alignment.",
                "next_agent": "OutreachAgent",
                "metadata": {
                    "execution_time": "calculated_by_supervisor",
                    "candidates_screened": len(candidates),
                    "pass_rate": round(len(screened_candidates) / len(candidates), 2) if candidates else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error screening candidates: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "candidates_screened": 0,
                "qualified_candidates": 0
            }

    
    def calculate_screening_score(
        self,
        candidate: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive screening score using weighted rubric
        
        Scoring Components:
        - Required Skills (35%): Match percentage of must-have skills
        - Experience (25%): Years of experience fit
        - Education (15%): Degree level match
        - Preferred Skills (15%): Match percentage of nice-to-have skills
        - Cultural Fit (10%): Indicators from profile
        
        Args:
            candidate: Candidate dict with skills, experience_years, education, etc.
            job_requirements: Job requirements dict
        
        Returns:
            Tuple of (overall_score, score_breakdown_dict)
        
        Example:
            >>> score, breakdown = agent.calculate_screening_score(
            ...     {"skills": ["Python", "AWS"], "experience_years": 7, ...},
            ...     {"required_skills": ["Python", "AWS", "React"], ...}
            ... )
            >>> print(f"Score: {score}, Breakdown: {breakdown}")
        """
        scores = {}
        
        # 1. Required Skills Score (35%)
        required_skills = set(job_requirements.get("required_skills", []))
        candidate_skills = set(candidate.get("skills", []))
        
        if required_skills:
            required_match = len(required_skills & candidate_skills)
            scores["required_skills"] = required_match / len(required_skills)
        else:
            scores["required_skills"] = 1.0  # No requirements = full score
        
        # 2. Experience Score (25%)
        exp_years = candidate.get("experience_years", 0)
        exp_requirements = job_requirements.get("experience_years", {})
        exp_min = exp_requirements.get("min", 0)
        exp_max = exp_requirements.get("max", 100)
        
        if exp_min <= exp_years <= exp_max:
            scores["experience"] = 1.0  # Perfect fit
        elif exp_years >= exp_min:
            # Over-qualified: slight penalty for retention risk
            over_years = exp_years - exp_max
            scores["experience"] = max(0.8, 1.0 - (over_years * 0.05))
        else:
            # Under-qualified: proportional score
            scores["experience"] = exp_years / exp_min if exp_min > 0 else 0.0
        
        # 3. Education Score (15%)
        scores["education"] = self._evaluate_education(
            candidate.get("education", ""),
            job_requirements.get("education", "")
        )
        
        # 4. Preferred Skills Score (15%)
        preferred_skills = set(job_requirements.get("preferred_skills", []))
        
        if preferred_skills:
            preferred_match = len(preferred_skills & candidate_skills)
            scores["preferred_skills"] = preferred_match / len(preferred_skills)
        else:
            scores["preferred_skills"] = 1.0  # No preferences = full score
        
        # 5. Cultural Fit Indicators (10%)
        scores["cultural_fit"] = self._assess_cultural_fit(
            candidate,
            job_requirements.get("cultural_values", [])
        )
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[category] * self.score_weights[category]
            for category in scores
        )
        
        return overall_score, scores
    
    def should_pass_screening(
        self,
        overall_score: float,
        score_breakdown: Dict[str, float],
        pass_threshold: float,
        require_all_must_haves: bool
    ) -> Tuple[bool, str]:
        """
        Determine if candidate passes screening
        
        Args:
            overall_score: Weighted overall score (0.0-1.0)
            score_breakdown: Individual component scores
            pass_threshold: Minimum overall score to pass (default 0.70)
            require_all_must_haves: If True, required_skills must be 1.0
        
        Returns:
            Tuple of (passed: bool, reason: str)
        
        Example:
            >>> passed, reason = agent.should_pass_screening(0.75, {...}, 0.70, True)
            >>> print(f"Passed: {passed}, Reason: {reason}")
        """
        # Check overall threshold
        if overall_score < pass_threshold:
            return False, f"Below overall threshold ({overall_score:.2f} < {pass_threshold})"
        
        # Check must-have requirements
        if require_all_must_haves:
            if score_breakdown.get("required_skills", 0) < 1.0:
                missing_pct = (1.0 - score_breakdown["required_skills"]) * 100
                return False, f"Missing {missing_pct:.0f}% of required skills"
        
        return True, "Passed screening"
    
    def _evaluate_education(self, candidate_education: str, required_education: str) -> float:
        """
        Evaluate education level match
        
        Education hierarchy: PhD > Master's > Bachelor's > Associate > High School
        
        Args:
            candidate_education: Candidate's education string
            required_education: Required education string
        
        Returns:
            Score from 0.0 to 1.0
        """
        education_levels = {
            "phd": 5,
            "doctorate": 5,
            "master": 4,
            "mba": 4,
            "bachelor": 3,
            "bs": 3,
            "ba": 3,
            "associate": 2,
            "high school": 1,
            "": 0
        }
        
        candidate_edu_lower = candidate_education.lower()
        required_edu_lower = required_education.lower()
        
        # Find candidate's education level
        candidate_level = 0
        for edu_key, level in education_levels.items():
            if edu_key in candidate_edu_lower:
                candidate_level = max(candidate_level, level)
        
        # Find required education level
        required_level = 0
        for edu_key, level in education_levels.items():
            if edu_key in required_edu_lower:
                required_level = max(required_level, level)
        
        # If no requirement specified, full score
        if required_level == 0:
            return 1.0
        
        # If candidate meets or exceeds requirement
        if candidate_level >= required_level:
            return 1.0
        
        # Partial credit for lower education
        return candidate_level / required_level if required_level > 0 else 0.0
    
    def _assess_cultural_fit(
        self,
        candidate: Dict[str, Any],
        cultural_values: List[str]
    ) -> float:
        """
        Assess cultural fit indicators from candidate profile
        
        This is a simplified assessment based on profile indicators.
        In production, this would use more sophisticated analysis.
        
        Args:
            candidate: Candidate dict
            cultural_values: List of cultural values to look for
        
        Returns:
            Score from 0.0 to 1.0
        """
        # For hackathon demo, use a baseline score
        # In production, this would analyze resume text, LinkedIn activity, etc.
        
        # Check for positive indicators
        indicators = 0
        total_indicators = 5
        
        # 1. Has notes/description (shows engagement)
        if candidate.get("notes"):
            indicators += 1
        
        # 2. Has GitHub (shows technical engagement)
        if candidate.get("github_url"):
            indicators += 1
        
        # 3. Has LinkedIn (shows professional presence)
        if candidate.get("linkedin_url"):
            indicators += 1
        
        # 4. Location flexibility (remote or willing to relocate)
        location = candidate.get("location", "").lower()
        if "remote" in location or "anywhere" in location:
            indicators += 1
        
        # 5. Experience level appropriate (not too junior, not too senior)
        exp_years = candidate.get("experience_years", 0)
        if 3 <= exp_years <= 15:
            indicators += 1
        
        return indicators / total_indicators

    
    def _analyze_candidate_profile(
        self,
        candidate: Dict[str, Any],
        job_requirements: Dict[str, Any],
        score_breakdown: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """
        Extract strengths and concerns from candidate profile
        
        Args:
            candidate: Candidate dict
            job_requirements: Job requirements dict
            score_breakdown: Score breakdown from calculate_screening_score
        
        Returns:
            Tuple of (strengths: List[str], concerns: List[str])
        """
        strengths = []
        concerns = []
        
        # Analyze skills
        required_skills = set(job_requirements.get("required_skills", []))
        preferred_skills = set(job_requirements.get("preferred_skills", []))
        candidate_skills = set(candidate.get("skills", []))
        
        matched_required = required_skills & candidate_skills
        matched_preferred = preferred_skills & candidate_skills
        missing_required = required_skills - candidate_skills
        
        if matched_required:
            strengths.append(f"Has {len(matched_required)}/{len(required_skills)} required skills: "
                           f"{', '.join(list(matched_required)[:3])}")
        
        if matched_preferred:
            strengths.append(f"Has preferred skills: {', '.join(list(matched_preferred)[:3])}")
        
        if missing_required:
            concerns.append(f"Missing required skills: {', '.join(list(missing_required)[:3])}")
        
        # Analyze experience
        exp_years = candidate.get("experience_years", 0)
        exp_requirements = job_requirements.get("experience_years", {})
        exp_min = exp_requirements.get("min", 0)
        exp_max = exp_requirements.get("max", 100)
        
        if exp_min <= exp_years <= exp_max:
            strengths.append(f"{exp_years} years experience (ideal range)")
        elif exp_years > exp_max:
            concerns.append(f"{exp_years} years experience (may be overqualified)")
        elif exp_years < exp_min:
            concerns.append(f"Only {exp_years} years experience (requires {exp_min}+)")
        
        # Analyze education
        if score_breakdown.get("education", 0) >= 1.0:
            strengths.append(f"Education: {candidate.get('education', 'N/A')}")
        elif score_breakdown.get("education", 0) < 0.8:
            concerns.append(f"Education below requirement: {candidate.get('education', 'N/A')}")
        
        # Analyze location
        candidate_location = candidate.get("location", "")
        job_location = job_requirements.get("location", "")
        
        if "remote" in candidate_location.lower() or "remote" in job_location.lower():
            strengths.append("Open to remote work")
        
        # Add notes if available
        if candidate.get("notes"):
            strengths.append(candidate["notes"][:100])  # First 100 chars
        
        # Limit to top 3 of each
        return strengths[:3], concerns[:3]
    
    def _generate_recommendation(
        self,
        overall_score: float,
        score_breakdown: Dict[str, float]
    ) -> str:
        """
        Generate hiring recommendation based on score
        
        Args:
            overall_score: Overall screening score
            score_breakdown: Individual component scores
        
        Returns:
            Recommendation string
        """
        if overall_score >= 0.85:
            return "Strong match - proceed to outreach immediately"
        elif overall_score >= 0.75:
            return "Good match - proceed to outreach"
        elif overall_score >= 0.70:
            return "Acceptable match - consider for outreach"
        else:
            return "Below threshold - do not proceed"
    
    def _calculate_confidence(self, score_breakdown: Dict[str, float]) -> float:
        """
        Calculate confidence in screening decision
        
        Higher confidence when scores are consistent across categories.
        Lower confidence when scores vary widely.
        
        Args:
            score_breakdown: Individual component scores
        
        Returns:
            Confidence score from 0.0 to 1.0
        """
        scores = list(score_breakdown.values())
        
        if not scores:
            return 0.5
        
        # Calculate variance
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        
        # Lower variance = higher confidence
        # Variance ranges from 0 (all same) to 0.25 (max spread)
        confidence = 1.0 - (variance * 2)  # Scale to 0.5-1.0 range
        
        return max(0.5, min(1.0, confidence))
    
    def _generate_screening_summary(
        self,
        qualified_candidates: List[Dict[str, Any]],
        disqualified_candidates: List[Dict[str, Any]],
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for screening results
        
        Args:
            qualified_candidates: List of candidates who passed
            disqualified_candidates: List of candidates who failed
            job_requirements: Job requirements dict
        
        Returns:
            Summary dict with statistics
        """
        total = len(qualified_candidates) + len(disqualified_candidates)
        
        if not qualified_candidates:
            return {
                "pass_rate": 0.0,
                "average_score": 0.0,
                "top_score": 0.0,
                "common_gaps": []
            }
        
        # Calculate statistics
        scores = [c["overall_score"] for c in qualified_candidates]
        pass_rate = len(qualified_candidates) / total if total > 0 else 0
        average_score = sum(scores) / len(scores)
        top_score = max(scores)
        
        # Identify common gaps from disqualified candidates
        gap_counts = {}
        for candidate in disqualified_candidates:
            for concern in candidate.get("concerns", []):
                # Extract skill name from concern
                if "Missing required skills:" in concern:
                    skills = concern.replace("Missing required skills:", "").strip()
                    for skill in skills.split(","):
                        skill = skill.strip()
                        gap_counts[skill] = gap_counts.get(skill, 0) + 1
        
        # Get top 3 common gaps
        common_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        common_gaps = [skill for skill, count in common_gaps]
        
        return {
            "pass_rate": round(pass_rate, 2),
            "average_score": round(average_score, 2),
            "top_score": round(top_score, 2),
            "common_gaps": common_gaps
        }
    
    def _save_screening_results(
        self,
        job_id: str,
        qualified_candidates: List[Dict[str, Any]]
    ) -> None:
        """
        Save screening results to DynamoDB
        
        Updates candidate records with screening scores and status.
        
        Args:
            job_id: Job ID
            qualified_candidates: List of qualified candidates with scores
        """
        try:
            for candidate in qualified_candidates:
                candidate_id = candidate.get("candidate_id")
                
                if not candidate_id:
                    continue
                
                # Update candidate record in DynamoDB
                update_data = {
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "screening_score": candidate["overall_score"],
                    "screening_rank": candidate["rank"],
                    "screening_status": "qualified",
                    "screening_timestamp": get_timestamp(),
                    "score_breakdown": candidate["score_breakdown"],
                    "strengths": candidate["strengths"],
                    "concerns": candidate["concerns"],
                    "recommendation": candidate["recommendation"]
                }
                
                save_to_dynamodb(Config.CANDIDATES_TABLE, update_data)
            
            logger.info(f"Saved screening results for {len(qualified_candidates)} candidates")
            
        except Exception as e:
            logger.error(f"Error saving screening results: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Screening Agent
    
    Event format:
    {
        "operation": "screen_candidates",
        "job_id": "job_001",
        "job_requirements": {...},
        "candidates": [{...}, {...}],
        "screening_parameters": {...}
    }
    
    Args:
        event: Lambda event dict
        context: Lambda context object
    
    Returns:
        Response dict with screening results
    """
    try:
        logger.info(f"Screening Agent Lambda invoked: {json.dumps(event)}")
        
        operation = event.get("operation")
        agent = ScreeningAgent()
        
        if operation == "screen_candidates":
            result = agent.screen_candidates(
                job_id=event.get("job_id"),
                job_requirements=event.get("job_requirements", {}),
                candidates=event.get("candidates", []),
                screening_parameters=event.get("screening_parameters")
            )
            return format_success_response(result)
        
        else:
            return format_error_response(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return format_error_response(str(e))


# For local testing
if __name__ == "__main__":
    # Test with sample data
    agent = ScreeningAgent()
    
    sample_job_requirements = {
        "title": "Senior Software Engineer",
        "required_skills": ["Python", "AWS", "React"],
        "preferred_skills": ["GraphQL", "Docker"],
        "experience_years": {"min": 5, "max": 10},
        "education": "Bachelor's in Computer Science",
        "location": "Seattle, WA or Remote"
    }
    
    sample_candidates = [
        {
            "candidate_id": "C001",
            "name": "Alice Johnson",
            "skills": ["Python", "AWS", "React", "GraphQL"],
            "experience_years": 7,
            "education": "BS Computer Science",
            "location": "Seattle, WA",
            "notes": "Strong full-stack background"
        },
        {
            "candidate_id": "C002",
            "name": "Bob Smith",
            "skills": ["Python", "AWS"],
            "experience_years": 4,
            "education": "BS Computer Science",
            "location": "Remote",
            "notes": "Backend specialist"
        }
    ]
    
    result = agent.screen_candidates(
        job_id="test_job_001",
        job_requirements=sample_job_requirements,
        candidates=sample_candidates,
        screening_parameters={"pass_threshold": 0.70, "top_n": 10}
    )
    
    print(json.dumps(result, indent=2))
