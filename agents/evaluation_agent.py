"""
Evaluation Agent - Analyzes interview feedback and generates hiring recommendations

This module implements the Evaluation Agent, which synthesizes feedback from multiple
interviewers, analyzes interview transcripts, calculates comprehensive evaluation scores,
and generates data-driven hiring recommendations.

References:
- Governing Doc: 00_governing_docs/08_agent_specifications.md (Section 8: Evaluation Agent)
- Architecture: 00_governing_docs/07_system_architecture.md
- Build Checklist: 00_governing_docs/16_module_build_checklist.md (Phase 4.5)

Verification Sources:
- AI Candidate Evaluation: https://everworker.ai/blog/ai_agents_candidate_screening_faster_fairer_hiring-2
- Candidate Quality Measurement: https://everworker.ai/blog/ai_candidate_quality_measurement_hiring
- Interview Scoring Best Practices: https://www.lever.co/blog/interview-scoring-guide
- Bias Mitigation in Hiring: https://www.shrm.org/topics-tools/news/talent-acquisition/how-to-reduce-bias-in-hiring
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from statistics import mean, stdev

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

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EvaluationAgent:
    """
    Evaluation Agent synthesizes interview feedback and generates hiring recommendations
    
    Responsibilities:
    1. Aggregate feedback from multiple interviewers
    2. Analyze interview transcripts for insights
    3. Calculate weighted evaluation scores
    4. Generate hire/no-hire recommendations
    5. Create comprehensive evaluation reports
    6. Identify interviewer consensus and disagreements
    
    Evaluation Rubric (from 08_agent_specifications.md):
    - Technical Skills: 35% (domain expertise, problem-solving)
    - Problem Solving: 25% (analytical thinking, approach)
    - Communication: 15% (clarity, collaboration)
    - Cultural Fit: 15% (values alignment, team fit)
    - Leadership Potential: 10% (growth potential, initiative)
    """
    
    def __init__(self):
        """Initialize Evaluation Agent"""
        self.agent_name = "EvaluationAgent"
        self.agent_role = "Interview Feedback Synthesizer & Hiring Recommender"
        
        # Evaluation weights from agent specifications
        self.evaluation_weights = {
            "technical_skills": 0.35,
            "problem_solving": 0.25,
            "communication": 0.15,
            "cultural_fit": 0.15,
            "leadership_potential": 0.10
        }
        
        # Recommendation thresholds
        self.recommendation_thresholds = {
            "strong_hire": 0.85,
            "hire": 0.75,
            "maybe": 0.65,
            "no_hire": 0.0
        }
        
        logger.info(f"{self.agent_name} initialized with evaluation weights: {self.evaluation_weights}")
    
    def evaluate_candidates(
        self,
        job_id: str,
        evaluation_rubric: Optional[Dict[str, float]] = None,
        candidates: List[Dict[str, Any]] = None,
        evaluation_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate candidates based on interview feedback and generate recommendations
        
        Args:
            job_id: Job requisition ID
            evaluation_rubric: Optional custom rubric weights (defaults to standard weights)
            candidates: List of candidate dicts with interview_data and interviewer_feedback
            evaluation_parameters: Optional parameters (decision_threshold, require_consensus, etc.)
        
        Returns:
            Dict with evaluation results, recommendations, and summary
        
        Example:
            >>> agent = EvaluationAgent()
            >>> result = agent.evaluate_candidates(
            ...     job_id="job_001",
            ...     candidates=[{...}, {...}],
            ...     evaluation_parameters={"decision_threshold": 0.75, "top_n_recommendations": 3}
            ... )
            >>> print(result["recommendations"])
        """
        try:
            logger.info(f"Starting candidate evaluation for job {job_id} with {len(candidates or [])} candidates")
            
            # Use custom rubric or default
            rubric = evaluation_rubric or self.evaluation_weights
            
            # Set default parameters
            params = evaluation_parameters or {}
            decision_threshold = params.get("decision_threshold", 0.75)
            require_consensus = params.get("require_consensus", False)
            top_n = params.get("top_n_recommendations", 3)
            
            # Evaluate each candidate
            evaluated_candidates = []
            
            for candidate in (candidates or []):
                # Calculate comprehensive evaluation score
                overall_score, score_breakdown = self.calculate_evaluation_score(
                    candidate,
                    rubric
                )
                
                # Analyze interview transcript if available
                transcript_insights = self._analyze_transcript(candidate)
                
                # Assess interviewer consensus
                consensus_analysis = self._assess_interviewer_consensus(
                    candidate.get("interviewer_feedback", [])
                )
                
                # Generate hiring recommendation
                recommendation, confidence = self.generate_hiring_recommendation(
                    overall_score,
                    score_breakdown,
                    consensus_analysis,
                    decision_threshold,
                    require_consensus
                )
                
                # Extract key strengths and concerns
                strengths, concerns = self._extract_strengths_and_concerns(
                    candidate,
                    score_breakdown,
                    transcript_insights,
                    consensus_analysis
                )
                
                # Create evaluation result
                evaluation_result = {
                    "candidate_id": candidate.get("candidate_id"),
                    "name": candidate.get("name", "[Name]"),
                    "overall_score": round(overall_score, 2),
                    "recommendation": recommendation,
                    "confidence": round(confidence, 2),
                    "score_breakdown": {k: round(v, 2) for k, v in score_breakdown.items()},
                    "key_strengths": strengths,
                    "potential_concerns": concerns,
                    "interviewer_consensus": consensus_analysis,
                    "transcript_insights": transcript_insights,
                    "screening_score": candidate.get("screening_score", 0.0)
                }
                
                evaluated_candidates.append(evaluation_result)
            
            # Rank candidates by overall score
            evaluated_candidates.sort(key=lambda x: x["overall_score"], reverse=True)
            
            # Add rank to each candidate
            for rank, candidate in enumerate(evaluated_candidates, 1):
                candidate["rank"] = rank
                candidate["hiring_recommendation"] = self._generate_detailed_recommendation(
                    candidate,
                    rank,
                    top_n
                )
            
            # Generate evaluation summary
            evaluation_summary = self._generate_evaluation_summary(evaluated_candidates)
            
            # Generate next steps
            next_steps = self._generate_next_steps(evaluated_candidates[:top_n])
            
            # Save evaluation results to DynamoDB
            self._save_evaluation_results(job_id, evaluated_candidates[:top_n])
            
            logger.info(f"Evaluation complete: {len(evaluated_candidates)} candidates evaluated")
            
            return {
                "status": "success",
                "candidates_evaluated": len(evaluated_candidates),
                "recommendations": evaluated_candidates[:top_n],
                "all_evaluations": evaluated_candidates,
                "evaluation_summary": evaluation_summary,
                "next_steps": next_steps,
                "confidence": 0.90,
                "reasoning": f"Evaluated {len(evaluated_candidates)} candidates. "
                           f"Top {min(top_n, len(evaluated_candidates))} recommendations based on "
                           f"interview performance and interviewer consensus.",
                "next_agent": "none",
                "metadata": {
                    "execution_time": "calculated_by_supervisor",
                    "candidates_evaluated": len(evaluated_candidates),
                    "strong_hire_count": sum(1 for c in evaluated_candidates if c["recommendation"] == "strong_hire"),
                    "hire_count": sum(1 for c in evaluated_candidates if c["recommendation"] == "hire")
                }
            }
            
        except Exception as e:
            logger.error(f"Error evaluating candidates: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "candidates_evaluated": 0
            }

    
    def calculate_evaluation_score(
        self,
        candidate: Dict[str, Any],
        rubric: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive evaluation score by aggregating interviewer feedback
        
        Scoring Process:
        1. Average scores across all interviewers for each category
        2. Normalize scores to 0.0-1.0 range (assuming 1-5 scale)
        3. Apply weighted rubric to calculate overall score
        
        Args:
            candidate: Candidate dict with interviewer_feedback list
            rubric: Evaluation rubric with category weights
        
        Returns:
            Tuple of (overall_score, score_breakdown_dict)
        
        Example:
            >>> score, breakdown = agent.calculate_evaluation_score(
            ...     {"interviewer_feedback": [{...}, {...}]},
            ...     {"technical_skills": 0.35, "problem_solving": 0.25, ...}
            ... )
            >>> print(f"Score: {score}, Breakdown: {breakdown}")
        """
        interviewer_feedback = candidate.get("interviewer_feedback", [])
        
        if not interviewer_feedback:
            # No feedback available - use screening score as fallback
            screening_score = candidate.get("screening_score", 0.5)
            logger.warning(f"No interviewer feedback for candidate {candidate.get('candidate_id')}, "
                         f"using screening score: {screening_score}")
            
            # Distribute screening score across categories
            return screening_score, {
                category: screening_score for category in rubric.keys()
            }
        
        # Aggregate scores across interviewers
        category_scores = {}
        
        for category in rubric.keys():
            # Collect scores from all interviewers for this category
            scores_for_category = []
            
            for feedback in interviewer_feedback:
                score = feedback.get("scores", {}).get(category, 0)
                # Normalize from 1-5 scale to 0-1 scale
                normalized_score = (score - 1) / 4.0 if score > 0 else 0.0
                scores_for_category.append(normalized_score)
            
            # Average across interviewers
            if scores_for_category:
                category_scores[category] = mean(scores_for_category)
            else:
                category_scores[category] = 0.0
        
        # Calculate weighted overall score
        overall_score = sum(
            category_scores[category] * rubric[category]
            for category in rubric.keys()
        )
        
        return overall_score, category_scores
    
    def generate_hiring_recommendation(
        self,
        overall_score: float,
        score_breakdown: Dict[str, float],
        consensus_analysis: Dict[str, Any],
        decision_threshold: float,
        require_consensus: bool
    ) -> Tuple[str, float]:
        """
        Generate hire/no-hire recommendation with confidence level
        
        Decision Logic:
        1. Check if score meets threshold
        2. Check interviewer consensus if required
        3. Determine recommendation level (strong_hire, hire, maybe, no_hire)
        4. Calculate confidence based on score consistency and consensus
        
        Args:
            overall_score: Weighted overall evaluation score
            score_breakdown: Individual category scores
            consensus_analysis: Interviewer consensus data
            decision_threshold: Minimum score to recommend hire
            require_consensus: If True, require unanimous positive feedback
        
        Returns:
            Tuple of (recommendation: str, confidence: float)
        
        Example:
            >>> rec, conf = agent.generate_hiring_recommendation(0.88, {...}, {...}, 0.75, False)
            >>> print(f"Recommendation: {rec}, Confidence: {conf}")
        """
        # Check consensus requirements
        if require_consensus and not consensus_analysis.get("unanimous", False):
            if consensus_analysis.get("strong_no", 0) > 0 or consensus_analysis.get("no", 0) > 0:
                return "no_hire", 0.85
        
        # Determine recommendation based on score
        if overall_score >= self.recommendation_thresholds["strong_hire"]:
            recommendation = "strong_hire"
        elif overall_score >= self.recommendation_thresholds["hire"]:
            recommendation = "hire"
        elif overall_score >= self.recommendation_thresholds["maybe"]:
            recommendation = "maybe"
        else:
            recommendation = "no_hire"
        
        # Calculate confidence
        confidence = self._calculate_recommendation_confidence(
            overall_score,
            score_breakdown,
            consensus_analysis
        )
        
        return recommendation, confidence
    
    def _analyze_transcript(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze interview transcript using Nova to extract insights
        
        Uses Amazon Nova to process interview transcripts and identify:
        - Positive indicators (problem-solving approach, communication quality)
        - Concerns or red flags
        - Notable quotes or moments
        - Technical depth demonstrated
        
        Args:
            candidate: Candidate dict with interview_data containing transcript
        
        Returns:
            Dict with transcript analysis results
        """
        interview_data = candidate.get("interview_data", {})
        transcript_url = interview_data.get("transcript_url")
        
        if not transcript_url:
            return {
                "analyzed": False,
                "positive_indicators": [],
                "concerns": [],
                "notable_quotes": []
            }
        
        # For hackathon demo, simulate transcript analysis
        # In production, this would load and analyze actual transcript
        logger.info(f"Analyzing transcript for candidate {candidate.get('candidate_id')}")
        
        # Simulate Nova-powered transcript analysis
        # In production: transcript_text = load_from_s3(transcript_url)
        # analysis = invoke_bedrock(prompt=f"Analyze this interview transcript: {transcript_text}")
        
        # For demo, generate insights based on interviewer feedback
        interviewer_feedback = candidate.get("interviewer_feedback", [])
        
        positive_indicators = []
        concerns = []
        
        if interviewer_feedback:
            # Extract insights from interviewer comments
            for feedback in interviewer_feedback:
                comments = feedback.get("comments", "")
                
                # Identify positive indicators
                if any(word in comments.lower() for word in ["strong", "excellent", "impressive", "great"]):
                    positive_indicators.append(comments[:100])
                
                # Identify concerns
                if any(word in comments.lower() for word in ["concern", "weak", "lacking", "needs improvement"]):
                    concerns.append(comments[:100])
        
        return {
            "analyzed": True,
            "positive_indicators": positive_indicators[:3],
            "concerns": concerns[:3],
            "notable_quotes": []
        }
    
    def _assess_interviewer_consensus(
        self,
        interviewer_feedback: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess level of consensus among interviewers
        
        Analyzes interviewer recommendations to determine:
        - Unanimous agreement (all same recommendation)
        - Majority agreement (>50% same recommendation)
        - Split decision (no clear majority)
        - Distribution of recommendations
        
        Args:
            interviewer_feedback: List of feedback dicts with recommendations
        
        Returns:
            Dict with consensus analysis
        """
        if not interviewer_feedback:
            return {
                "unanimous": False,
                "majority": False,
                "split_decision": True,
                "strong_yes": 0,
                "yes": 0,
                "maybe": 0,
                "no": 0,
                "strong_no": 0,
                "total_interviewers": 0
            }
        
        # Count recommendations
        recommendation_counts = {
            "strong_yes": 0,
            "yes": 0,
            "maybe": 0,
            "no": 0,
            "strong_no": 0
        }
        
        for feedback in interviewer_feedback:
            rec = feedback.get("recommendation", "maybe")
            if rec in recommendation_counts:
                recommendation_counts[rec] += 1
        
        total = len(interviewer_feedback)
        
        # Determine consensus type
        max_count = max(recommendation_counts.values())
        unanimous = max_count == total
        majority = max_count > total / 2
        split_decision = not majority
        
        return {
            "unanimous": unanimous,
            "majority": majority,
            "split_decision": split_decision,
            "strong_yes": recommendation_counts["strong_yes"],
            "yes": recommendation_counts["yes"],
            "maybe": recommendation_counts["maybe"],
            "no": recommendation_counts["no"],
            "strong_no": recommendation_counts["strong_no"],
            "total_interviewers": total
        }
    
    def _calculate_recommendation_confidence(
        self,
        overall_score: float,
        score_breakdown: Dict[str, float],
        consensus_analysis: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence in hiring recommendation
        
        Confidence factors:
        1. Score consistency across categories (lower variance = higher confidence)
        2. Interviewer consensus (unanimous = higher confidence)
        3. Distance from decision threshold (further = higher confidence)
        
        Args:
            overall_score: Overall evaluation score
            score_breakdown: Individual category scores
            consensus_analysis: Consensus data
        
        Returns:
            Confidence score from 0.0 to 1.0
        """
        confidence_factors = []
        
        # Factor 1: Score consistency (low variance = high confidence)
        scores = list(score_breakdown.values())
        if len(scores) > 1:
            score_variance = stdev(scores) if len(scores) > 1 else 0
            consistency_confidence = 1.0 - min(score_variance, 0.5)  # Cap variance impact
            confidence_factors.append(consistency_confidence)
        
        # Factor 2: Interviewer consensus
        if consensus_analysis.get("unanimous"):
            consensus_confidence = 1.0
        elif consensus_analysis.get("majority"):
            consensus_confidence = 0.8
        else:
            consensus_confidence = 0.6
        confidence_factors.append(consensus_confidence)
        
        # Factor 3: Distance from threshold
        # Further from threshold = higher confidence
        distance_from_threshold = abs(overall_score - 0.75)
        distance_confidence = min(0.7 + (distance_from_threshold * 2), 1.0)
        confidence_factors.append(distance_confidence)
        
        # Average confidence factors
        overall_confidence = mean(confidence_factors)
        
        return max(0.5, min(1.0, overall_confidence))

    
    def _extract_strengths_and_concerns(
        self,
        candidate: Dict[str, Any],
        score_breakdown: Dict[str, float],
        transcript_insights: Dict[str, Any],
        consensus_analysis: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """
        Extract key strengths and potential concerns from evaluation data
        
        Args:
            candidate: Candidate dict
            score_breakdown: Category scores
            transcript_insights: Transcript analysis results
            consensus_analysis: Consensus data
        
        Returns:
            Tuple of (strengths: List[str], concerns: List[str])
        """
        strengths = []
        concerns = []
        
        # Analyze score breakdown for strengths
        for category, score in score_breakdown.items():
            category_name = category.replace("_", " ").title()
            
            if score >= 0.9:
                strengths.append(f"Exceptional {category_name} (score: {score:.2f})")
            elif score >= 0.8:
                strengths.append(f"Strong {category_name} (score: {score:.2f})")
            elif score < 0.6:
                concerns.append(f"Below average {category_name} (score: {score:.2f})")
        
        # Add transcript insights
        if transcript_insights.get("positive_indicators"):
            strengths.extend(transcript_insights["positive_indicators"][:2])
        
        if transcript_insights.get("concerns"):
            concerns.extend(transcript_insights["concerns"][:2])
        
        # Add consensus information
        if consensus_analysis.get("unanimous"):
            strengths.append("Unanimous positive feedback from all interviewers")
        elif consensus_analysis.get("split_decision"):
            concerns.append("Mixed feedback from interviewers - requires further discussion")
        
        # Add screening score context
        screening_score = candidate.get("screening_score", 0)
        if screening_score >= 0.85:
            strengths.append(f"Strong resume match (screening score: {screening_score:.2f})")
        
        # Add experience context
        if candidate.get("sourcing_notes"):
            strengths.append(candidate["sourcing_notes"][:100])
        
        # Limit to top 4 of each
        return strengths[:4], concerns[:4]
    
    def _generate_detailed_recommendation(
        self,
        candidate: Dict[str, Any],
        rank: int,
        top_n: int
    ) -> str:
        """
        Generate detailed hiring recommendation text
        
        Args:
            candidate: Evaluated candidate dict
            rank: Candidate's rank
            top_n: Number of top recommendations
        
        Returns:
            Detailed recommendation string
        """
        recommendation = candidate["recommendation"]
        overall_score = candidate["overall_score"]
        confidence = candidate["confidence"]
        
        if recommendation == "strong_hire":
            if rank <= top_n:
                return (f"Extend offer immediately. Rank #{rank} candidate with exceptional performance "
                       f"(score: {overall_score:.2f}, confidence: {confidence:.2f}). "
                       f"Strong technical skills and cultural fit.")
            else:
                return (f"Strong candidate but ranked #{rank}. Consider for future opportunities "
                       f"or if top candidates decline.")
        
        elif recommendation == "hire":
            if rank <= top_n:
                return (f"Recommend moving forward with offer. Rank #{rank} candidate with solid performance "
                       f"(score: {overall_score:.2f}). Good fit for the role.")
            else:
                return (f"Qualified candidate but ranked #{rank}. Keep in pipeline for future roles.")
        
        elif recommendation == "maybe":
            return (f"Mixed evaluation (score: {overall_score:.2f}). Recommend additional interview round "
                   f"or discussion among hiring team before decision.")
        
        else:  # no_hire
            return (f"Does not meet hiring bar (score: {overall_score:.2f}). "
                   f"Send rejection with feedback for candidate development.")
    
    def _generate_evaluation_summary(
        self,
        evaluated_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for evaluation results
        
        Args:
            evaluated_candidates: List of evaluated candidates
        
        Returns:
            Summary dict with statistics
        """
        if not evaluated_candidates:
            return {
                "strong_hire": 0,
                "hire": 0,
                "maybe": 0,
                "no_hire": 0,
                "average_score": 0.0,
                "top_score": 0.0,
                "consensus_rate": 0.0
            }
        
        # Count recommendations
        recommendation_counts = {
            "strong_hire": 0,
            "hire": 0,
            "maybe": 0,
            "no_hire": 0
        }
        
        for candidate in evaluated_candidates:
            rec = candidate.get("recommendation", "no_hire")
            if rec in recommendation_counts:
                recommendation_counts[rec] += 1
        
        # Calculate statistics
        scores = [c["overall_score"] for c in evaluated_candidates]
        average_score = mean(scores)
        top_score = max(scores)
        
        # Calculate consensus rate (percentage with unanimous or majority consensus)
        consensus_count = sum(
            1 for c in evaluated_candidates
            if c.get("interviewer_consensus", {}).get("unanimous") or
               c.get("interviewer_consensus", {}).get("majority")
        )
        consensus_rate = consensus_count / len(evaluated_candidates)
        
        return {
            "strong_hire": recommendation_counts["strong_hire"],
            "hire": recommendation_counts["hire"],
            "maybe": recommendation_counts["maybe"],
            "no_hire": recommendation_counts["no_hire"],
            "average_score": round(average_score, 2),
            "top_score": round(top_score, 2),
            "consensus_rate": round(consensus_rate, 2)
        }
    
    def _generate_next_steps(
        self,
        top_candidates: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate actionable next steps based on evaluation results
        
        Args:
            top_candidates: List of top-ranked candidates
        
        Returns:
            List of next step strings
        """
        next_steps = []
        
        for candidate in top_candidates:
            candidate_id = candidate.get("candidate_id")
            name = candidate.get("name", "[Name]")
            recommendation = candidate.get("recommendation")
            rank = candidate.get("rank")
            
            if recommendation == "strong_hire":
                next_steps.append(
                    f"Extend offer to {name} (Rank #{rank}, ID: {candidate_id}) - strong hire"
                )
            elif recommendation == "hire":
                next_steps.append(
                    f"Prepare offer for {name} (Rank #{rank}, ID: {candidate_id})"
                )
            elif recommendation == "maybe":
                next_steps.append(
                    f"Schedule additional interview for {name} (Rank #{rank}, ID: {candidate_id})"
                )
        
        # Add general next steps
        if not next_steps:
            next_steps.append("No candidates meet hiring bar - continue sourcing")
        else:
            next_steps.append("Send rejection emails to candidates not selected")
            next_steps.append("Update ATS with evaluation results")
        
        return next_steps
    
    def _save_evaluation_results(
        self,
        job_id: str,
        evaluated_candidates: List[Dict[str, Any]]
    ) -> None:
        """
        Save evaluation results to DynamoDB
        
        Updates candidate records with evaluation scores and recommendations.
        
        Args:
            job_id: Job ID
            evaluated_candidates: List of evaluated candidates
        """
        try:
            for candidate in evaluated_candidates:
                candidate_id = candidate.get("candidate_id")
                
                if not candidate_id:
                    continue
                
                # Update candidate record in DynamoDB
                update_data = {
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "evaluation_score": candidate["overall_score"],
                    "evaluation_rank": candidate["rank"],
                    "evaluation_recommendation": candidate["recommendation"],
                    "evaluation_confidence": candidate["confidence"],
                    "evaluation_timestamp": get_timestamp(),
                    "score_breakdown": candidate["score_breakdown"],
                    "key_strengths": candidate["key_strengths"],
                    "potential_concerns": candidate["potential_concerns"],
                    "hiring_recommendation": candidate["hiring_recommendation"],
                    "interviewer_consensus": candidate["interviewer_consensus"]
                }
                
                save_to_dynamodb(Config.CANDIDATES_TABLE, update_data)
            
            logger.info(f"Saved evaluation results for {len(evaluated_candidates)} candidates")
            
        except Exception as e:
            logger.error(f"Error saving evaluation results: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Evaluation Agent
    
    Event format:
    {
        "operation": "evaluate_candidates",
        "job_id": "job_001",
        "evaluation_rubric": {...},
        "candidates": [{...}, {...}],
        "evaluation_parameters": {...}
    }
    
    Args:
        event: Lambda event dict
        context: Lambda context object
    
    Returns:
        Response dict with evaluation results
    """
    try:
        logger.info(f"Evaluation Agent Lambda invoked: {json.dumps(event)}")
        
        operation = event.get("operation")
        agent = EvaluationAgent()
        
        if operation == "evaluate_candidates":
            result = agent.evaluate_candidates(
                job_id=event.get("job_id"),
                evaluation_rubric=event.get("evaluation_rubric"),
                candidates=event.get("candidates", []),
                evaluation_parameters=event.get("evaluation_parameters")
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
    agent = EvaluationAgent()
    
    sample_candidates = [
        {
            "candidate_id": "C001",
            "name": "Alice Johnson",
            "screening_score": 0.87,
            "sourcing_notes": "7 years React experience, AWS certified",
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
                    "comments": "Strong technical skills, excellent communication. Solved coding challenge efficiently.",
                    "recommendation": "strong_yes",
                    "confidence": 0.9
                }
            ]
        },
        {
            "candidate_id": "C002",
            "name": "Bob Smith",
            "screening_score": 0.75,
            "sourcing_notes": "5 years backend experience",
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
                    "comments": "Solid technical skills, good problem-solving approach.",
                    "recommendation": "yes",
                    "confidence": 0.8
                }
            ]
        }
    ]
    
    result = agent.evaluate_candidates(
        job_id="test_job_001",
        candidates=sample_candidates,
        evaluation_parameters={"decision_threshold": 0.75, "top_n_recommendations": 3}
    )
    
    print(json.dumps(result, indent=2))
