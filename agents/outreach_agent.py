"""
Outreach Agent - Personalized Candidate Communication

The Outreach Agent generates personalized, compelling outreach messages for qualified
candidates. It uses Amazon Nova to craft messages that highlight candidate strengths,
align with job opportunities, and maximize response rates.

Core Responsibilities:
- Generate personalized outreach messages using Nova
- Support multiple channels (email, LinkedIn InMail)
- Apply tone and style controls (professional, friendly, enthusiastic)
- Personalize based on candidate strengths and job fit
- Track outreach attempts and timing
- Save messages to DynamoDB for record-keeping

References:
- 08_agent_specifications.md: Outreach Agent detailed requirements (Section 6)
- 07_system_architecture.md: Multi-agent workflow architecture
- 09_agent_coordination_protocol.md: Inter-agent handoff protocol
- 16_module_build_checklist.md: Phase 4.3 implementation requirements

Verification Sources:
- Recruiting Email Best Practices: https://www.lever.co/blog/recruiting-email-templates
- LinkedIn InMail Tips: https://business.linkedin.com/talent-solutions/resources/recruiting-tips/inmail-best-practices
- Personalization in Recruiting: https://www.smartrecruiters.com/blog/personalized-recruiting-messages
- Response Rate Optimization: https://www.greenhouse.io/blog/candidate-outreach-best-practices
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

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
    generate_id,
    truncate_text
)
from shared.config import Config
from shared.models import Candidate, Interaction, InteractionType, CandidateStatus

logger = logging.getLogger()
logger.setLevel(Config.LOG_LEVEL)


class OutreachAgent:
    """
    Outreach Agent for personalized candidate communication
    
    The Outreach Agent uses Amazon Nova to generate compelling, personalized
    messages that:
    1. Highlight candidate's relevant strengths and experience
    2. Connect candidate background to job opportunity
    3. Use appropriate tone and style for the audience
    4. Include clear call-to-action
    5. Optimize for response rates
    
    Workflow:
        Qualified Candidates → Message Generation → Personalization →
        Channel Selection → Outreach Tracking → Candidate Pipeline
    """
    
    def __init__(self):
        """Initialize Outreach Agent"""
        self.agent_name = "OutreachAgent"
        self.supported_channels = ["email", "linkedin", "phone"]
        
        # Message templates for different tones
        self.tone_guidelines = {
            "professional": "Formal, respectful, business-focused",
            "friendly": "Warm, approachable, conversational",
            "enthusiastic": "Energetic, exciting, opportunity-focused",
            "casual": "Relaxed, informal, authentic"
        }
        
        log_agent_execution(
            self.agent_name,
            "Initialized",
            {"supported_channels": self.supported_channels}
        )
    
    def generate_outreach(
        self,
        job_id: str,
        job_details: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        outreach_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized outreach messages for qualified candidates
        
        Args:
            job_id: Job ID
            job_details: Job information (title, description, requirements, etc.)
            candidates: List of qualified candidates with screening results
            outreach_parameters: Optional parameters (channel, tone, template, etc.)
            
        Returns:
            Dict with outreach results and tracking information
            
        Example:
            >>> agent = OutreachAgent()
            >>> result = agent.generate_outreach(
            >>>     "job-123",
            >>>     {
            >>>         "title": "Senior Software Engineer",
            >>>         "company": "TechCorp",
            >>>         "description": "Build scalable systems...",
            >>>         "requirements": {"required_skills": ["Python", "AWS"]}
            >>>     },
            >>>     [
            >>>         {
            >>>             "candidate_id": "cand-001",
            >>>             "name": "Alice Johnson",
            >>>             "strengths": ["Python expert", "AWS certified"],
            >>>             "screening_score": 0.92
            >>>         }
            >>>     ],
            >>>     {"channel": "email", "tone": "professional"}
            >>> )
        """
        log_agent_execution(
            self.agent_name,
            "Starting outreach generation",
            {"job_id": job_id, "candidate_count": len(candidates)}
        )
        
        try:
            # Set default parameters
            params = outreach_parameters or {}
            channel = params.get("channel", "email")
            tone = params.get("tone", "professional")
            include_salary = params.get("include_salary", False)
            max_length = params.get("max_length", 300)  # words
            
            # Validate channel
            if channel not in self.supported_channels:
                return format_error_response(
                    f"Unsupported channel: {channel}",
                    {"supported_channels": self.supported_channels},
                    "InvalidChannel"
                )
            
            # Generate outreach for each candidate
            outreach_results = []
            total_input_tokens = 0
            total_output_tokens = 0
            
            for candidate in candidates:
                # Generate personalized message
                message_result = self.generate_personalized_message(
                    candidate=candidate,
                    job_details=job_details,
                    channel=channel,
                    tone=tone,
                    max_length=max_length,
                    include_salary=include_salary
                )
                
                if not message_result['success']:
                    logger.warning(
                        f"Failed to generate message for candidate {candidate.get('candidate_id')}: "
                        f"{message_result.get('error')}"
                    )
                    continue
                
                # Track token usage
                total_input_tokens += message_result.get('input_tokens', 0)
                total_output_tokens += message_result.get('output_tokens', 0)
                
                # Save outreach message and interaction
                save_result = self._save_outreach_message(
                    candidate_id=candidate.get('candidate_id'),
                    job_id=job_id,
                    message=message_result['message'],
                    subject=message_result.get('subject'),
                    channel=channel,
                    metadata=message_result.get('metadata', {})
                )
                
                if save_result['success']:
                    outreach_results.append({
                        "candidate_id": candidate.get('candidate_id'),
                        "candidate_name": candidate.get('name'),
                        "channel": channel,
                        "subject": message_result.get('subject'),
                        "message": message_result['message'],
                        "message_length": len(message_result['message'].split()),
                        "personalization_score": message_result.get('personalization_score', 0.8),
                        "status": "sent"
                    })
            
            # Calculate outreach summary
            outreach_summary = {
                "total_candidates": len(candidates),
                "messages_generated": len(outreach_results),
                "success_rate": len(outreach_results) / len(candidates) if candidates else 0,
                "channel": channel,
                "tone": tone,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_cost_usd": Config.calculate_cost(total_input_tokens, total_output_tokens)
            }
            
            log_agent_execution(
                self.agent_name,
                "Outreach generation completed",
                {
                    "messages_generated": len(outreach_results),
                    "cost": f"${outreach_summary['total_cost_usd']:.4f}"
                }
            )
            
            return format_success_response(
                {
                    "messages_generated": len(outreach_results),
                    "outreach_results": outreach_results,
                    "outreach_summary": outreach_summary,
                    "next_agent": "SchedulingAgent"
                },
                {
                    "job_id": job_id,
                    "channel": channel,
                    "tone": tone
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating outreach: {str(e)}")
            return format_error_response(
                f"Failed to generate outreach: {str(e)}",
                {"job_id": job_id},
                "OutreachGenerationFailed"
            )

    
    def generate_personalized_message(
        self,
        candidate: Dict[str, Any],
        job_details: Dict[str, Any],
        channel: str,
        tone: str,
        max_length: int,
        include_salary: bool
    ) -> Dict[str, Any]:
        """
        Generate personalized outreach message for a single candidate
        
        Uses Amazon Nova to create a compelling message that:
        - Addresses candidate by name
        - References their specific strengths and experience
        - Connects their background to the job opportunity
        - Uses appropriate tone and style
        - Includes clear call-to-action
        
        Args:
            candidate: Candidate information with strengths and screening results
            job_details: Job information
            channel: Communication channel (email, linkedin, phone)
            tone: Message tone (professional, friendly, enthusiastic, casual)
            max_length: Maximum message length in words
            include_salary: Whether to include salary information
            
        Returns:
            Dict with message, subject, and metadata
            
        Example:
            >>> result = agent.generate_personalized_message(
            >>>     {"name": "Alice", "strengths": ["Python expert"]},
            >>>     {"title": "Senior Engineer", "company": "TechCorp"},
            >>>     "email",
            >>>     "professional",
            >>>     250,
            >>>     False
            >>> )
        """
        log_agent_execution(
            self.agent_name,
            "Generating personalized message",
            {"candidate": candidate.get('name'), "channel": channel, "tone": tone}
        )
        
        try:
            # Build system prompt for Nova
            system_prompt = self._build_system_prompt(channel, tone)
            
            # Build user prompt with candidate and job details
            user_prompt = self._build_user_prompt(
                candidate=candidate,
                job_details=job_details,
                max_length=max_length,
                include_salary=include_salary
            )
            
            # Invoke Nova to generate message
            nova_result = invoke_bedrock(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Higher temperature for creative, personalized messages
                max_tokens=1500
            )
            
            if not nova_result['success']:
                return {
                    'success': False,
                    'error': nova_result.get('error', 'Nova invocation failed')
                }
            
            # Parse Nova's response
            message_data = self._parse_nova_response(nova_result['content'], channel)
            
            # Calculate personalization score
            personalization_score = self._calculate_personalization_score(
                message_data['message'],
                candidate
            )
            
            return {
                'success': True,
                'subject': message_data.get('subject'),
                'message': message_data['message'],
                'call_to_action': message_data.get('call_to_action'),
                'personalization_score': personalization_score,
                'input_tokens': nova_result.get('input_tokens', 0),
                'output_tokens': nova_result.get('output_tokens', 0),
                'cost_usd': nova_result.get('cost_usd', 0),
                'metadata': {
                    'tone': tone,
                    'channel': channel,
                    'word_count': len(message_data['message'].split())
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_system_prompt(self, channel: str, tone: str) -> str:
        """
        Build system prompt for Nova based on channel and tone
        
        Args:
            channel: Communication channel
            tone: Message tone
            
        Returns:
            System prompt string
        """
        tone_description = self.tone_guidelines.get(tone, "professional and respectful")
        
        system_prompt = f"""You are an expert recruiting outreach specialist. Your goal is to write compelling, personalized messages that attract top talent and maximize response rates.

Channel: {channel.upper()}
Tone: {tone.upper()} ({tone_description})

Guidelines:
1. Personalization: Reference specific candidate strengths, skills, and experience
2. Value Proposition: Clearly articulate why this opportunity is exciting and relevant
3. Authenticity: Sound genuine, not templated or robotic
4. Brevity: Be concise and respect the candidate's time
5. Call-to-Action: Include a clear, low-friction next step
6. Professionalism: Maintain appropriate tone while being engaging

"""
        
        if channel == "email":
            system_prompt += """
Email-Specific Guidelines:
- Include a compelling subject line (5-8 words)
- Start with a personalized greeting
- Keep paragraphs short (2-3 sentences)
- Use bullet points for key details if needed
- End with a clear call-to-action
- Include professional signature placeholder

Format your response as JSON:
{
  "subject": "Subject line here",
  "message": "Full email body here",
  "call_to_action": "Specific next step"
}
"""
        elif channel == "linkedin":
            system_prompt += """
LinkedIn InMail Guidelines:
- No subject line needed (LinkedIn provides context)
- Start with a brief, personalized opening
- Keep total message under 200 words
- Reference LinkedIn profile or mutual connections if relevant
- Be conversational and authentic
- End with a simple question or invitation

Format your response as JSON:
{
  "message": "Full InMail message here",
  "call_to_action": "Specific next step"
}
"""
        else:  # phone
            system_prompt += """
Phone Script Guidelines:
- Brief introduction (who you are, company)
- Quick value proposition (why calling)
- Respect their time (ask if it's a good time)
- Key talking points (2-3 bullet points)
- Clear next step

Format your response as JSON:
{
  "message": "Phone script here",
  "call_to_action": "Specific next step"
}
"""
        
        return system_prompt
    
    def _build_user_prompt(
        self,
        candidate: Dict[str, Any],
        job_details: Dict[str, Any],
        max_length: int,
        include_salary: bool
    ) -> str:
        """
        Build user prompt with candidate and job details
        
        Args:
            candidate: Candidate information
            job_details: Job information
            max_length: Maximum message length in words
            include_salary: Whether to include salary
            
        Returns:
            User prompt string
        """
        # Extract candidate details
        candidate_name = candidate.get('name', '[Candidate Name]')
        candidate_title = candidate.get('current_title', 'professional')
        candidate_company = candidate.get('current_company', '')
        strengths = candidate.get('strengths', [])
        screening_score = candidate.get('screening_score', 0)
        
        # Extract job details
        job_title = job_details.get('title', 'Position')
        company_name = job_details.get('company', 'Our Company')
        job_description = job_details.get('description', '')
        location = job_details.get('location', 'Location TBD')
        remote_allowed = job_details.get('remote_allowed', False)
        
        # Build prompt
        prompt = f"""Generate a personalized outreach message for this candidate:

CANDIDATE INFORMATION:
- Name: {candidate_name}
- Current Role: {candidate_title}"""
        
        if candidate_company:
            prompt += f"\n- Current Company: {candidate_company}"
        
        prompt += f"\n- Screening Score: {screening_score:.0%} match"
        
        if strengths:
            prompt += f"\n- Key Strengths: {', '.join(strengths[:3])}"
        
        prompt += f"""

JOB OPPORTUNITY:
- Position: {job_title}
- Company: {company_name}
- Location: {location}"""
        
        if remote_allowed:
            prompt += " (Remote options available)"
        
        if include_salary and job_details.get('salary_range'):
            salary_range = job_details['salary_range']
            prompt += f"\n- Salary Range: ${salary_range.get('min', 0):,.0f} - ${salary_range.get('max', 0):,.0f}"
        
        # Add job description snippet
        if job_description:
            description_snippet = truncate_text(job_description, 200)
            prompt += f"\n- Description: {description_snippet}"
        
        prompt += f"""

REQUIREMENTS:
- Maximum length: {max_length} words
- Personalize based on candidate's strengths and experience
- Highlight why this opportunity is a great fit for them specifically
- Make it compelling and authentic
- Include a clear, low-friction call-to-action

Generate the message now in the specified JSON format."""
        
        return prompt
    
    def _parse_nova_response(self, content: str, channel: str) -> Dict[str, Any]:
        """
        Parse Nova's JSON response into structured message data
        
        Args:
            content: Nova's response content
            channel: Communication channel
            
        Returns:
            Dict with subject, message, and call_to_action
        """
        try:
            # Try to parse as JSON
            message_data = json.loads(content)
            
            # Validate required fields
            if 'message' not in message_data:
                raise ValueError("Missing 'message' field in Nova response")
            
            return {
                'subject': message_data.get('subject'),
                'message': message_data['message'],
                'call_to_action': message_data.get('call_to_action')
            }
            
        except json.JSONDecodeError:
            # If not valid JSON, treat entire content as message
            logger.warning("Nova response was not valid JSON, using raw content")
            
            # Try to extract subject line if it's an email
            if channel == "email" and "Subject:" in content:
                lines = content.split('\n')
                subject = None
                message_lines = []
                
                for line in lines:
                    if line.startswith("Subject:"):
                        subject = line.replace("Subject:", "").strip()
                    else:
                        message_lines.append(line)
                
                return {
                    'subject': subject,
                    'message': '\n'.join(message_lines).strip(),
                    'call_to_action': None
                }
            
            return {
                'subject': None,
                'message': content.strip(),
                'call_to_action': None
            }
    
    def _calculate_personalization_score(
        self,
        message: str,
        candidate: Dict[str, Any]
    ) -> float:
        """
        Calculate how personalized the message is
        
        Checks for:
        - Candidate name mentioned
        - Specific skills or strengths referenced
        - Current company or role mentioned
        - Generic phrases avoided
        
        Args:
            message: Generated message
            candidate: Candidate information
            
        Returns:
            Personalization score (0.0 to 1.0)
        """
        score = 0.0
        message_lower = message.lower()
        
        # Check for candidate name (20%)
        candidate_name = candidate.get('name', '').lower()
        if candidate_name and candidate_name in message_lower:
            score += 0.20
        
        # Check for specific skills/strengths (30%)
        strengths = candidate.get('strengths', [])
        if strengths:
            mentioned_strengths = sum(
                1 for strength in strengths
                if strength.lower() in message_lower
            )
            score += min(0.30, (mentioned_strengths / len(strengths)) * 0.30)
        
        # Check for current role or company (20%)
        current_title = candidate.get('current_title', '').lower()
        current_company = candidate.get('current_company', '').lower()
        
        if current_title and current_title in message_lower:
            score += 0.10
        if current_company and current_company in message_lower:
            score += 0.10
        
        # Check for generic phrases (negative score)
        generic_phrases = [
            "dear sir/madam",
            "to whom it may concern",
            "we are looking for",
            "great opportunity",
            "competitive salary"
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase in message_lower)
        if generic_count == 0:
            score += 0.30  # Bonus for avoiding generic language
        else:
            score -= generic_count * 0.10  # Penalty for generic phrases
        
        return max(0.0, min(1.0, score))

    
    def _save_outreach_message(
        self,
        candidate_id: str,
        job_id: str,
        message: str,
        subject: Optional[str],
        channel: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save outreach message to DynamoDB
        
        Creates an Interaction record and updates Candidate status.
        
        Args:
            candidate_id: Candidate ID
            job_id: Job ID
            message: Outreach message content
            subject: Email subject (if applicable)
            channel: Communication channel
            metadata: Additional metadata
            
        Returns:
            Dict with success status
        """
        try:
            # Create Interaction record
            interaction = Interaction(
                candidate_id=candidate_id,
                job_id=job_id,
                interaction_type=InteractionType.OUTREACH_SENT,
                agent_name=self.agent_name,
                subject=subject,
                message=message,
                metadata={
                    'channel': channel,
                    **metadata
                }
            )
            
            # Save interaction to DynamoDB
            save_result = save_to_dynamodb(
                Config.INTERACTIONS_TABLE,
                interaction.to_dynamodb_item()
            )
            
            if not save_result['success']:
                logger.error(f"Failed to save interaction: {save_result.get('error')}")
                return save_result
            
            # Update candidate status and last_contacted_at
            update_result = update_dynamodb_item(
                Config.CANDIDATES_TABLE,
                {'candidateId': candidate_id},
                {
                    'status': CandidateStatus.OUTREACH_SENT,
                    'lastContactedAt': get_timestamp(),
                    'outreachMessage': message
                }
            )
            
            if not update_result['success']:
                logger.warning(f"Failed to update candidate status: {update_result.get('error')}")
            
            log_agent_execution(
                self.agent_name,
                "Outreach message saved",
                {"candidate_id": candidate_id, "channel": channel}
            )
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error saving outreach message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_follow_up_message(
        self,
        candidate_id: str,
        job_id: str,
        original_message: str,
        days_since_outreach: int,
        tone: str = "friendly"
    ) -> Dict[str, Any]:
        """
        Generate follow-up message for non-responsive candidates
        
        Args:
            candidate_id: Candidate ID
            job_id: Job ID
            original_message: Original outreach message
            days_since_outreach: Days since original outreach
            tone: Message tone
            
        Returns:
            Dict with follow-up message
            
        Example:
            >>> result = agent.generate_follow_up_message(
            >>>     "cand-001",
            >>>     "job-123",
            >>>     "Hi Alice, I wanted to reach out...",
            >>>     7,
            >>>     "friendly"
            >>> )
        """
        log_agent_execution(
            self.agent_name,
            "Generating follow-up message",
            {"candidate_id": candidate_id, "days_since": days_since_outreach}
        )
        
        try:
            # Get candidate details
            candidate_data = get_from_dynamodb(
                Config.CANDIDATES_TABLE,
                {'candidateId': candidate_id}
            )
            
            if not candidate_data:
                return format_error_response(
                    "Candidate not found",
                    {"candidate_id": candidate_id},
                    "CandidateNotFound"
                )
            
            # Build system prompt for follow-up
            system_prompt = f"""You are a recruiting outreach specialist writing a follow-up message.

Tone: {tone.upper()}

Guidelines for follow-ups:
1. Be brief and respectful of their time
2. Acknowledge they may be busy
3. Add new information or value (not just "checking in")
4. Make it easy to respond (yes/no question)
5. Provide an easy opt-out
6. Keep it under 100 words

Format as JSON:
{{
  "subject": "Brief subject line",
  "message": "Follow-up message"
}}
"""
            
            # Build user prompt
            user_prompt = f"""Generate a follow-up message for a candidate who hasn't responded.

Original outreach was {days_since_outreach} days ago.

Candidate: {candidate_data.get('name')}
Position: {candidate_data.get('jobTitle', 'the position')}

Original message snippet:
{truncate_text(original_message, 150)}

Generate a brief, respectful follow-up that:
- Acknowledges they may be busy
- Adds new value or information
- Makes it easy to respond or opt-out
- Stays under 100 words
"""
            
            # Invoke Nova
            nova_result = invoke_bedrock(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=800
            )
            
            if not nova_result['success']:
                return format_error_response(
                    "Failed to generate follow-up message",
                    {"error": nova_result.get('error')},
                    "NovaInvocationFailed"
                )
            
            # Parse response
            message_data = self._parse_nova_response(nova_result['content'], "email")
            
            return format_success_response(
                {
                    "subject": message_data.get('subject'),
                    "message": message_data['message'],
                    "follow_up_number": 1,  # Could track this in metadata
                    "recommended_wait_days": 7  # Wait another week if no response
                },
                {
                    "candidate_id": candidate_id,
                    "input_tokens": nova_result.get('input_tokens', 0),
                    "output_tokens": nova_result.get('output_tokens', 0),
                    "cost_usd": nova_result.get('cost_usd', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating follow-up message: {str(e)}")
            return format_error_response(
                f"Failed to generate follow-up: {str(e)}",
                {"candidate_id": candidate_id},
                "FollowUpGenerationFailed"
            )
    
    def batch_generate_outreach(
        self,
        job_id: str,
        job_details: Dict[str, Any],
        candidate_ids: List[str],
        outreach_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate outreach for multiple candidates by ID (batch operation)
        
        Args:
            job_id: Job ID
            job_details: Job information
            candidate_ids: List of candidate IDs
            outreach_parameters: Optional parameters
            
        Returns:
            Dict with batch results
        """
        log_agent_execution(
            self.agent_name,
            "Starting batch outreach generation",
            {"job_id": job_id, "candidate_count": len(candidate_ids)}
        )
        
        try:
            # Retrieve candidates from DynamoDB
            candidates = []
            for candidate_id in candidate_ids:
                candidate_data = get_from_dynamodb(
                    Config.CANDIDATES_TABLE,
                    {'candidateId': candidate_id}
                )
                
                if candidate_data:
                    candidates.append(candidate_data)
                else:
                    logger.warning(f"Candidate not found: {candidate_id}")
            
            # Generate outreach for retrieved candidates
            return self.generate_outreach(
                job_id=job_id,
                job_details=job_details,
                candidates=candidates,
                outreach_parameters=outreach_parameters
            )
            
        except Exception as e:
            logger.error(f"Error in batch outreach generation: {str(e)}")
            return format_error_response(
                f"Batch outreach failed: {str(e)}",
                {"job_id": job_id},
                "BatchOutreachFailed"
            )
    
    def get_outreach_analytics(
        self,
        job_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get outreach analytics for a job
        
        Args:
            job_id: Job ID
            days: Number of days to analyze
            
        Returns:
            Dict with analytics data
        """
        log_agent_execution(
            self.agent_name,
            "Retrieving outreach analytics",
            {"job_id": job_id, "days": days}
        )
        
        try:
            # Query interactions for this job
            # Note: This would use a GSI on jobId in production
            # For hackathon demo, we'll return mock analytics
            
            analytics = {
                "job_id": job_id,
                "period_days": days,
                "total_outreach_sent": 0,
                "response_rate": 0.0,
                "average_response_time_hours": 0,
                "by_channel": {
                    "email": {"sent": 0, "responses": 0, "response_rate": 0.0},
                    "linkedin": {"sent": 0, "responses": 0, "response_rate": 0.0}
                },
                "by_tone": {
                    "professional": {"sent": 0, "responses": 0},
                    "friendly": {"sent": 0, "responses": 0},
                    "enthusiastic": {"sent": 0, "responses": 0}
                },
                "top_performing_messages": []
            }
            
            return format_success_response(
                analytics,
                {"job_id": job_id}
            )
            
        except Exception as e:
            logger.error(f"Error retrieving analytics: {str(e)}")
            return format_error_response(
                f"Failed to retrieve analytics: {str(e)}",
                {"job_id": job_id},
                "AnalyticsRetrievalFailed"
            )


# ============================================================================
# Lambda Handler (for AWS Lambda deployment)
# ============================================================================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Outreach Agent
    
    Supported operations:
    - generate_outreach: Generate outreach messages for candidates
    - generate_follow_up: Generate follow-up message for non-responsive candidate
    - batch_generate_outreach: Generate outreach for multiple candidates by ID
    - get_outreach_analytics: Get outreach performance analytics
    
    Args:
        event: Lambda event with operation and parameters
        context: Lambda context
        
    Returns:
        Dict with operation result
        
    Example event:
        {
            "operation": "generate_outreach",
            "job_id": "job-123",
            "job_details": {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "description": "...",
                "requirements": {...}
            },
            "candidates": [
                {
                    "candidate_id": "cand-001",
                    "name": "Alice Johnson",
                    "strengths": ["Python expert", "AWS certified"],
                    "screening_score": 0.92
                }
            ],
            "outreach_parameters": {
                "channel": "email",
                "tone": "professional",
                "max_length": 250
            }
        }
    """
    agent = OutreachAgent()
    
    operation = event.get('operation')
    
    if operation == 'generate_outreach':
        return agent.generate_outreach(
            job_id=event['job_id'],
            job_details=event['job_details'],
            candidates=event['candidates'],
            outreach_parameters=event.get('outreach_parameters')
        )
    
    elif operation == 'generate_follow_up':
        return agent.generate_follow_up_message(
            candidate_id=event['candidate_id'],
            job_id=event['job_id'],
            original_message=event['original_message'],
            days_since_outreach=event['days_since_outreach'],
            tone=event.get('tone', 'friendly')
        )
    
    elif operation == 'batch_generate_outreach':
        return agent.batch_generate_outreach(
            job_id=event['job_id'],
            job_details=event['job_details'],
            candidate_ids=event['candidate_ids'],
            outreach_parameters=event.get('outreach_parameters')
        )
    
    elif operation == 'get_outreach_analytics':
        return agent.get_outreach_analytics(
            job_id=event['job_id'],
            days=event.get('days', 30)
        )
    
    else:
        return format_error_response(
            f"Unknown operation: {operation}",
            {"operation": operation},
            "UnknownOperation"
        )


# For local testing
if __name__ == "__main__":
    # Test with sample data
    agent = OutreachAgent()
    
    sample_job_details = {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "description": "We're looking for a talented engineer to build scalable cloud systems using Python and AWS.",
        "location": "Seattle, WA",
        "remote_allowed": True,
        "requirements": {
            "required_skills": ["Python", "AWS", "React"],
            "experience_years": {"min": 5, "max": 10}
        },
        "salary_range": {"min": 140000, "max": 180000}
    }
    
    sample_candidates = [
        {
            "candidate_id": "cand-001",
            "name": "Alice Johnson",
            "current_title": "Software Engineer",
            "current_company": "CloudTech Inc",
            "strengths": [
                "Python expert with 7 years experience",
                "AWS certified solutions architect",
                "Strong React skills"
            ],
            "screening_score": 0.92
        }
    ]
    
    result = agent.generate_outreach(
        job_id="test_job_001",
        job_details=sample_job_details,
        candidates=sample_candidates,
        outreach_parameters={
            "channel": "email",
            "tone": "professional",
            "max_length": 250,
            "include_salary": True
        }
    )
    
    print(json.dumps(result, indent=2))
