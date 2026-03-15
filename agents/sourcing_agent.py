"""
Sourcing Agent - Candidate Discovery and Initial Matching

The Sourcing Agent is the first worker agent in the recruiting pipeline. It discovers
potential candidates from multiple talent sources, applies initial filtering, and ranks
candidates by fit score. This agent focuses on quantity and breadth, leaving detailed
evaluation to the Screening Agent.

Core Responsibilities:
- Discover candidates from multiple sources (LinkedIn, GitHub, job boards)
- Construct intelligent Boolean search queries
- Extract structured data from candidate profiles
- Calculate initial match scores based on job requirements
- Rank and filter candidates by relevance
- Build candidate pipeline for screening stage

References:
- 08_agent_specifications.md: Sourcing Agent detailed requirements
- 07_system_architecture.md: Multi-agent workflow architecture
- 09_agent_coordination_protocol.md: Inter-agent handoff protocol
- 16_module_build_checklist.md: Phase 4.1 implementation requirements

Verification Sources:
- AI Sourcing for Recruiters: https://capyhax.com/posts/ai-sourcing-recruiters-complete-guide
- Boolean Search Automation: https://everworker.ai/blog/automate_boolean_search_recruiting_sourcing_engine
- LinkedIn Recruiter Best Practices: https://business.linkedin.com/talent-solutions/resources/talent-acquisition/recruiting-tips
- Candidate Matching Algorithms: https://www.hiretual.com/blog/candidate-matching-algorithm
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import re

from shared.utils import (
    invoke_bedrock,
    save_to_dynamodb,
    get_from_dynamodb,
    update_dynamodb_item,
    format_error_response,
    format_success_response,
    log_agent_execution,
    track_agent_cost,
    get_timestamp,
    generate_id
)
from shared.config import Config
from shared.models import Candidate, Job, CandidateStatus

logger = logging.getLogger()
logger.setLevel(Config.LOG_LEVEL)


class SourcingAgent:
    """
    Sourcing Agent for discovering and ranking candidates
    
    The sourcing agent implements intelligent candidate discovery using:
    1. Boolean search query construction for multiple platforms
    2. Amazon Nova for semantic matching and profile extraction
    3. Weighted scoring algorithm for candidate ranking
    4. Multi-source aggregation (LinkedIn, GitHub, job boards)
    
    Workflow:
        Job Requirements → Boolean Search → Profile Discovery → 
        Match Scoring → Ranking → Candidate Pipeline
    """
    
    def __init__(self):
        """Initialize Sourcing Agent"""
        self.agent_name = "SourcingAgent"
        self.supported_sources = ["linkedin", "github", "indeed", "dice", "internal_db"]
        
        # Match score weights (from agent specifications)
        self.score_weights = {
            "required_skills": 0.40,
            "experience": 0.25,
            "location": 0.15,
            "education": 0.10,
            "preferred_skills": 0.10
        }
        
        log_agent_execution(
            self.agent_name,
            "Initialized",
            {"supported_sources": self.supported_sources}
        )

    
    def source_candidates(
        self,
        job_id: str,
        job_requirements: Dict[str, Any],
        sourcing_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method to discover and rank candidates for a job
        
        Args:
            job_id: Job ID to source candidates for
            job_requirements: Job requirements including skills, experience, location
            sourcing_parameters: Optional parameters (target_count, sources, min_score)
            
        Returns:
            Dict with discovered candidates and sourcing metrics
            
        Example:
            >>> agent = SourcingAgent()
            >>> result = agent.source_candidates(
            >>>     "job-123",
            >>>     {
            >>>         "title": "Senior Software Engineer",
            >>>         "required_skills": ["Python", "AWS", "React"],
            >>>         "experience_years": {"min": 5, "max": 10},
            >>>         "location": "Seattle, WA or Remote"
            >>>     },
            >>>     {"target_count": 50, "sources": ["linkedin", "github"]}
            >>> )
        """
        log_agent_execution(
            self.agent_name,
            "Starting candidate sourcing",
            {"job_id": job_id, "target_count": sourcing_parameters.get("target_count", 50)}
        )
        
        try:
            # Set default parameters
            params = sourcing_parameters or {}
            target_count = params.get("target_count", 50)
            sources = params.get("sources", ["linkedin", "github"])
            min_score = params.get("min_match_score", 0.6)
            
            # Construct Boolean search queries for each source
            search_queries = self._construct_search_queries(job_requirements, sources)
            
            # Discover candidates from multiple sources
            discovered_candidates = self._discover_candidates(
                search_queries,
                job_requirements,
                target_count
            )
            
            # Calculate match scores for each candidate
            scored_candidates = []
            for candidate_data in discovered_candidates:
                match_score = self.calculate_match_score(candidate_data, job_requirements)
                
                # Filter by minimum score
                if match_score >= min_score:
                    candidate_data["match_score"] = match_score
                    scored_candidates.append(candidate_data)
            
            # Rank candidates by match score
            ranked_candidates = self._rank_candidates(scored_candidates)
            
            # Take top N candidates
            top_candidates = ranked_candidates[:target_count]
            
            # Save candidates to DynamoDB
            saved_candidates = []
            for candidate_data in top_candidates:
                candidate = self._create_candidate_record(candidate_data, job_id)
                save_result = save_to_dynamodb(
                    Config.CANDIDATES_TABLE,
                    candidate.to_dynamodb_item()
                )
                
                if save_result['success']:
                    saved_candidates.append(candidate.to_dict())
            
            # Calculate sourcing metrics
            sourcing_summary = {
                "total_profiles_reviewed": len(discovered_candidates),
                "candidates_meeting_criteria": len(scored_candidates),
                "candidates_sourced": len(saved_candidates),
                "match_rate": len(scored_candidates) / len(discovered_candidates) if discovered_candidates else 0,
                "sources_used": sources,
                "average_match_score": sum(c["match_score"] for c in top_candidates) / len(top_candidates) if top_candidates else 0
            }
            
            log_agent_execution(
                self.agent_name,
                "Candidate sourcing completed",
                {
                    "candidates_found": len(saved_candidates),
                    "match_rate": f"{sourcing_summary['match_rate']:.2%}",
                    "avg_score": f"{sourcing_summary['average_match_score']:.2f}"
                }
            )
            
            return format_success_response(
                {
                    "candidates_found": len(saved_candidates),
                    "candidates": saved_candidates,
                    "sourcing_summary": sourcing_summary,
                    "next_agent": "ScreeningAgent"
                },
                {
                    "job_id": job_id,
                    "search_queries": search_queries
                }
            )
            
        except Exception as e:
            logger.error(f"Error sourcing candidates: {str(e)}")
            return format_error_response(
                f"Failed to source candidates: {str(e)}",
                {"job_id": job_id},
                "SourcingFailed"
            )

    
    def calculate_match_score(
        self,
        candidate_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> float:
        """
        Calculate match score between candidate and job requirements
        
        Uses weighted scoring algorithm:
        - Required skills: 40%
        - Experience years: 25%
        - Location match: 15%
        - Education: 10%
        - Preferred skills: 10%
        
        Args:
            candidate_data: Candidate profile data
            job_requirements: Job requirements
            
        Returns:
            Match score between 0.0 and 1.0
            
        Example:
            >>> agent = SourcingAgent()
            >>> score = agent.calculate_match_score(
            >>>     {"skills": ["Python", "AWS"], "experience_years": 6},
            >>>     {"required_skills": ["Python", "AWS", "React"], "experience_years": {"min": 5}}
            >>> )
            >>> print(f"Match score: {score:.2f}")
        """
        score = 0.0
        
        # Required Skills Score (40%)
        required_skills = set(s.lower() for s in job_requirements.get("required_skills", []))
        candidate_skills = set(s.lower() for s in candidate_data.get("skills", []))
        
        if required_skills:
            required_match = len(required_skills & candidate_skills)
            required_score = required_match / len(required_skills)
            score += required_score * self.score_weights["required_skills"]
        
        # Experience Years Score (25%)
        exp_years = candidate_data.get("experience_years", 0)
        exp_requirements = job_requirements.get("experience_years", {})
        exp_min = exp_requirements.get("min", 0)
        exp_max = exp_requirements.get("max", 100)
        
        if exp_min <= exp_years <= exp_max:
            exp_score = 1.0
        elif exp_years >= exp_min:
            # Over-qualified: slight penalty for retention risk
            exp_score = max(0.8, 1.0 - (exp_years - exp_max) * 0.05)
        else:
            # Under-qualified: proportional score
            exp_score = exp_years / exp_min if exp_min > 0 else 0
        
        score += exp_score * self.score_weights["experience"]
        
        # Location Match Score (15%)
        candidate_location = candidate_data.get("location", "").lower()
        job_location = job_requirements.get("location", "").lower()
        
        location_score = 0.0
        if "remote" in job_location or "remote" in candidate_location:
            location_score = 1.0
        elif self._locations_match(candidate_location, job_location):
            location_score = 1.0
        elif self._same_state(candidate_location, job_location):
            location_score = 0.7
        
        score += location_score * self.score_weights["location"]
        
        # Education Score (10%)
        candidate_education = candidate_data.get("education", "").lower()
        required_education = job_requirements.get("education", "").lower()
        
        education_score = self._evaluate_education(candidate_education, required_education)
        score += education_score * self.score_weights["education"]
        
        # Preferred Skills Score (10%)
        preferred_skills = set(s.lower() for s in job_requirements.get("preferred_skills", []))
        
        if preferred_skills:
            preferred_match = len(preferred_skills & candidate_skills)
            preferred_score = preferred_match / len(preferred_skills)
            score += preferred_score * self.score_weights["preferred_skills"]
        else:
            # If no preferred skills, give full credit
            score += self.score_weights["preferred_skills"]
        
        return min(score, 1.0)  # Cap at 1.0
    
    def construct_boolean_search(self, job_requirements: Dict[str, Any]) -> str:
        """
        Construct Boolean search query for job requirements
        
        Args:
            job_requirements: Job requirements
            
        Returns:
            Boolean search query string
            
        Example:
            >>> agent = SourcingAgent()
            >>> query = agent.construct_boolean_search({
            >>>     "title": "Senior Software Engineer",
            >>>     "required_skills": ["Python", "AWS"],
            >>>     "location": "Seattle, WA"
            >>> })
            >>> print(query)
            "Senior Software Engineer" AND (Python AND AWS) AND location:"Seattle, WA"
        """
        query_parts = []
        
        # Job title
        title = job_requirements.get("title", "")
        if title:
            query_parts.append(f'"{title}"')
        
        # Required skills (AND logic)
        required_skills = job_requirements.get("required_skills", [])
        if required_skills:
            skills_query = " AND ".join(required_skills)
            query_parts.append(f"({skills_query})")
        
        # Preferred skills (OR logic)
        preferred_skills = job_requirements.get("preferred_skills", [])
        if preferred_skills:
            preferred_query = " OR ".join(preferred_skills)
            query_parts.append(f"({preferred_query})")
        
        # Location
        location = job_requirements.get("location", "")
        if location and "remote" not in location.lower():
            query_parts.append(f'location:"{location}"')
        
        return " AND ".join(query_parts)

    
    def _construct_search_queries(
        self,
        job_requirements: Dict[str, Any],
        sources: List[str]
    ) -> Dict[str, str]:
        """
        Construct search queries for each source platform
        
        Args:
            job_requirements: Job requirements
            sources: List of source platforms
            
        Returns:
            Dict mapping source to search query
        """
        queries = {}
        
        for source in sources:
            if source == "linkedin":
                queries[source] = self.construct_boolean_search(job_requirements)
            elif source == "github":
                # GitHub search focuses on skills/languages
                skills = job_requirements.get("required_skills", [])
                queries[source] = " ".join(skills[:3])  # Top 3 skills
            elif source in ["indeed", "dice"]:
                queries[source] = self.construct_boolean_search(job_requirements)
            else:
                queries[source] = job_requirements.get("title", "")
        
        return queries
    
    def _discover_candidates(
        self,
        search_queries: Dict[str, str],
        job_requirements: Dict[str, Any],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """
        Discover candidates using Amazon Nova to simulate multi-source search
        
        For hackathon demo, we use Nova to generate realistic candidate profiles
        instead of calling real APIs (LinkedIn, GitHub, etc.)
        
        Args:
            search_queries: Search queries for each source
            job_requirements: Job requirements
            target_count: Target number of candidates
            
        Returns:
            List of candidate profile dictionaries
        """
        log_agent_execution(
            self.agent_name,
            "Discovering candidates",
            {"target_count": target_count, "sources": list(search_queries.keys())}
        )
        
        # Build prompt for Nova to generate candidate profiles
        system_prompt = """You are a recruiting data generator. Generate realistic candidate profiles that match job requirements with varying degrees of fit. Include candidates with different skill combinations, experience levels, and backgrounds to simulate real-world sourcing results."""
        
        prompt = f"""Generate {target_count} realistic candidate profiles for this job:

Job Title: {job_requirements.get('title', 'N/A')}
Required Skills: {', '.join(job_requirements.get('required_skills', []))}
Preferred Skills: {', '.join(job_requirements.get('preferred_skills', []))}
Experience: {job_requirements.get('experience_years', {}).get('min', 0)}-{job_requirements.get('experience_years', {}).get('max', 10)} years
Location: {job_requirements.get('location', 'N/A')}
Education: {job_requirements.get('education', 'N/A')}

Generate a diverse set of candidates with:
- 60% strong matches (have most required skills)
- 30% moderate matches (have some required skills)
- 10% weak matches (have few required skills)

Return a JSON array with this structure:
[
  {{
    "name": "[Full Name]",
    "current_title": "job title",
    "current_company": "company name",
    "location": "city, state",
    "experience_years": number,
    "skills": ["skill1", "skill2", ...],
    "education": "degree, university",
    "linkedin_url": "https://linkedin.com/in/...",
    "github_url": "https://github.com/..." (if applicable),
    "source": "linkedin|github|indeed",
    "summary": "brief professional summary"
  }}
]

Generate exactly {target_count} candidates."""

        try:
            # Invoke Nova to generate candidate profiles
            nova_result = invoke_bedrock(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher temperature for diversity
                max_tokens=8000
            )
            
            if not nova_result['success']:
                logger.warning(f"Nova invocation failed: {nova_result.get('error')}")
                return self._generate_fallback_candidates(job_requirements, target_count)
            
            # Parse Nova's response
            try:
                candidates = json.loads(nova_result['content'])
                if isinstance(candidates, list):
                    log_agent_execution(
                        self.agent_name,
                        "Candidates discovered via Nova",
                        {"count": len(candidates), "cost": f"${nova_result.get('cost_usd', 0):.4f}"}
                    )
                    return candidates
                else:
                    logger.warning("Nova response was not a list")
                    return self._generate_fallback_candidates(job_requirements, target_count)
            except json.JSONDecodeError:
                logger.warning("Failed to parse Nova response as JSON")
                return self._generate_fallback_candidates(job_requirements, target_count)
                
        except Exception as e:
            logger.error(f"Error discovering candidates: {str(e)}")
            return self._generate_fallback_candidates(job_requirements, target_count)

    
    def _generate_fallback_candidates(
        self,
        job_requirements: Dict[str, Any],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback candidate data if Nova fails
        
        Args:
            job_requirements: Job requirements
            count: Number of candidates to generate
            
        Returns:
            List of basic candidate profiles
        """
        candidates = []
        required_skills = job_requirements.get("required_skills", [])
        
        for i in range(count):
            # Vary skill coverage
            if i < count * 0.6:  # 60% strong matches
                skills = required_skills + job_requirements.get("preferred_skills", [])[:2]
            elif i < count * 0.9:  # 30% moderate matches
                skills = required_skills[:len(required_skills)//2]
            else:  # 10% weak matches
                skills = required_skills[:1]
            
            candidates.append({
                "name": f"[Candidate {i+1:03d}]",
                "current_title": job_requirements.get("title", "Software Engineer"),
                "current_company": f"Tech Company {i+1}",
                "location": job_requirements.get("location", "Remote"),
                "experience_years": job_requirements.get("experience_years", {}).get("min", 5) + (i % 5),
                "skills": skills,
                "education": job_requirements.get("education", "Bachelor's Degree"),
                "linkedin_url": f"https://linkedin.com/in/candidate{i+1}",
                "github_url": f"https://github.com/candidate{i+1}" if "github" in str(required_skills).lower() else None,
                "source": "linkedin",
                "summary": f"Experienced professional with {len(skills)} relevant skills"
            })
        
        return candidates
    
    def _rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank candidates by match score (descending)
        
        Args:
            candidates: List of candidates with match_score field
            
        Returns:
            Sorted list of candidates
        """
        return sorted(candidates, key=lambda c: c.get("match_score", 0), reverse=True)
    
    def _create_candidate_record(
        self,
        candidate_data: Dict[str, Any],
        job_id: str
    ) -> Candidate:
        """
        Create Candidate model instance from candidate data
        
        Args:
            candidate_data: Raw candidate data
            job_id: Associated job ID
            
        Returns:
            Candidate model instance
        """
        return Candidate(
            job_id=job_id,
            name=candidate_data.get("name", "[Name]"),
            email=candidate_data.get("email", f"{candidate_data.get('name', 'candidate').replace(' ', '.').lower()}@example.com"),
            phone=candidate_data.get("phone", "+1-555-0100"),
            location=candidate_data.get("location", "Unknown"),
            current_title=candidate_data.get("current_title", ""),
            current_company=candidate_data.get("current_company", ""),
            experience_years=candidate_data.get("experience_years", 0),
            skills=candidate_data.get("skills", []),
            education=candidate_data.get("education", ""),
            resume_url=candidate_data.get("resume_url"),
            linkedin_url=candidate_data.get("linkedin_url"),
            github_url=candidate_data.get("github_url"),
            source=candidate_data.get("source", "linkedin"),
            status=CandidateStatus.SOURCED,
            match_score=candidate_data.get("match_score", 0.0),
            notes=candidate_data.get("summary", "")
        )
    
    def _locations_match(self, loc1: str, loc2: str) -> bool:
        """Check if two locations match (city level)"""
        # Simple matching - can be enhanced with geocoding
        loc1_clean = re.sub(r'[^\w\s]', '', loc1.lower())
        loc2_clean = re.sub(r'[^\w\s]', '', loc2.lower())
        return loc1_clean in loc2_clean or loc2_clean in loc1_clean
    
    def _same_state(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are in the same state"""
        # Extract state abbreviations or names
        states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
        
        loc1_upper = loc1.upper()
        loc2_upper = loc2.upper()
        
        for state in states:
            if state in loc1_upper and state in loc2_upper:
                return True
        
        return False
    
    def _evaluate_education(self, candidate_edu: str, required_edu: str) -> float:
        """
        Evaluate education match
        
        Args:
            candidate_edu: Candidate's education
            required_edu: Required education
            
        Returns:
            Education score (0.0 to 1.0)
        """
        if not required_edu or "bachelor" not in required_edu.lower():
            return 1.0  # No specific requirement
        
        candidate_edu_lower = candidate_edu.lower()
        
        # PhD > Master's > Bachelor's > Associate > High School
        if "phd" in candidate_edu_lower or "doctorate" in candidate_edu_lower:
            return 1.0
        elif "master" in candidate_edu_lower or "mba" in candidate_edu_lower:
            return 1.0
        elif "bachelor" in candidate_edu_lower or "bs" in candidate_edu_lower or "ba" in candidate_edu_lower:
            return 1.0
        elif "associate" in candidate_edu_lower:
            return 0.7
        else:
            return 0.5  # Some education or equivalent experience



# ============================================================================
# Lambda Handler (for AWS Lambda deployment)
# ============================================================================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Sourcing Agent
    
    Supported operations:
    - source_candidates: Discover and rank candidates for a job
    - calculate_match_score: Calculate match score for a single candidate
    - construct_boolean_search: Generate Boolean search query
    
    Args:
        event: Lambda event with operation and parameters
        context: Lambda context
        
    Returns:
        Dict with operation result
        
    Example event:
        {
            "operation": "source_candidates",
            "job_id": "job-123",
            "job_requirements": {
                "title": "Senior Software Engineer",
                "required_skills": ["Python", "AWS"],
                "experience_years": {"min": 5, "max": 10}
            },
            "sourcing_parameters": {
                "target_count": 50,
                "sources": ["linkedin", "github"]
            }
        }
    """
    agent = SourcingAgent()
    
    operation = event.get('operation')
    
    if operation == 'source_candidates':
        return agent.source_candidates(
            job_id=event['job_id'],
            job_requirements=event['job_requirements'],
            sourcing_parameters=event.get('sourcing_parameters')
        )
    
    elif operation == 'calculate_match_score':
        score = agent.calculate_match_score(
            candidate_data=event['candidate_data'],
            job_requirements=event['job_requirements']
        )
        return format_success_response(
            {"match_score": score},
            {"candidate_id": event.get('candidate_id')}
        )
    
    elif operation == 'construct_boolean_search':
        query = agent.construct_boolean_search(
            job_requirements=event['job_requirements']
        )
        return format_success_response(
            {"boolean_query": query},
            {"job_id": event.get('job_id')}
        )
    
    else:
        return format_error_response(
            f"Unknown operation: {operation}",
            {"operation": operation},
            "UnknownOperation"
        )
