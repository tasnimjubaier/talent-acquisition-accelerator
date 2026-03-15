"""
Mock Bedrock Service for Local Development

Simulates Amazon Bedrock Nova API responses without AWS costs.
Generates realistic candidate profiles, screening evaluations, and other
recruiting-related content for local testing.

Usage:
    from local_dev.mock_bedrock import MockBedrockClient
    
    client = MockBedrockClient()
    response = client.converse(
        modelId='amazon.nova-lite-v1:0',
        messages=[{"role": "user", "content": [{"text": "Generate candidate profile"}]}]
    )

References:
- 02_tech_stack_decisions.md: Nova 2 Lite specifications
- 17_testing_strategy.md: Local testing approach
"""

import json
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime


class MockBedrockClient:
    """
    Mock Bedrock Runtime client that simulates Nova API responses
    
    This mock generates realistic responses for recruiting tasks:
    - Candidate profile generation
    - Resume screening and evaluation
    - Personalized outreach messages
    - Interview scheduling
    - Hiring recommendations
    """
    
    def __init__(self, latency_ms: int = 500):
        """
        Initialize mock Bedrock client
        
        Args:
            latency_ms: Simulated API latency in milliseconds
        """
        self.latency_ms = latency_ms
        self.call_count = 0
        
    def converse(
        self,
        modelId: str,
        messages: List[Dict[str, Any]],
        system: Optional[List[Dict[str, str]]] = None,
        inferenceConfig: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mock Bedrock Converse API
        
        Args:
            modelId: Model identifier (e.g., 'amazon.nova-lite-v1:0')
            messages: List of message objects
            system: Optional system prompt
            inferenceConfig: Optional inference configuration
            
        Returns:
            Mock response matching Bedrock Converse API format
        """
        self.call_count += 1
        
        # Simulate API latency
        time.sleep(self.latency_ms / 1000.0)
        
        # Extract user prompt
        user_message = messages[-1] if messages else {}
        content_blocks = user_message.get('content', [])
        prompt = content_blocks[0].get('text', '') if content_blocks else ''
        
        # Generate response based on prompt content
        response_text = self._generate_response(prompt, system)
        
        # Calculate token counts (rough estimation)
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(response_text)
        
        # Return mock response in Bedrock format
        return {
            'output': {
                'message': {
                    'role': 'assistant',
                    'content': [
                        {
                            'text': response_text
                        }
                    ]
                }
            },
            'usage': {
                'inputTokens': input_tokens,
                'outputTokens': output_tokens,
                'totalTokens': input_tokens + output_tokens
            },
            'stopReason': 'end_turn',
            'ResponseMetadata': {
                'RequestId': f'mock-request-{self.call_count}',
                'HTTPStatusCode': 200
            }
        }

    def _generate_response(self, prompt: str, system: Optional[List[Dict]] = None) -> str:
        """Generate realistic response based on prompt content"""
        prompt_lower = prompt.lower()
        
        # Candidate sourcing/generation
        if 'generate' in prompt_lower and 'candidate' in prompt_lower:
            return self._generate_candidate_profile()
        
        # Resume screening
        elif 'screen' in prompt_lower or 'evaluate' in prompt_lower:
            return self._generate_screening_evaluation()
        
        # Outreach message
        elif 'outreach' in prompt_lower or 'message' in prompt_lower or 'email' in prompt_lower:
            return self._generate_outreach_message()
        
        # Interview scheduling
        elif 'schedule' in prompt_lower or 'interview' in prompt_lower:
            return self._generate_scheduling_response()
        
        # Hiring evaluation
        elif 'recommend' in prompt_lower or 'hire' in prompt_lower or 'decision' in prompt_lower:
            return self._generate_hiring_recommendation()
        
        # Default response
        else:
            return self._generate_generic_response(prompt)
    
    def _generate_candidate_profile(self) -> str:
        """Generate realistic candidate profile"""
        names = [
            "Sarah Chen", "Michael Rodriguez", "Priya Patel", "James Wilson",
            "Emily Thompson", "David Kim", "Maria Garcia", "Alex Johnson",
            "Jessica Lee", "Robert Brown", "Aisha Mohammed", "Chris Anderson"
        ]
        
        titles = [
            "Senior Software Engineer", "Full Stack Developer", "Backend Engineer",
            "Frontend Developer", "DevOps Engineer", "Data Engineer",
            "Machine Learning Engineer", "Software Architect"
        ]
        
        companies = [
            "Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix",
            "Uber", "Airbnb", "Stripe", "Shopify", "Salesforce", "Adobe"
        ]
        
        skills_pool = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS",
            "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "Redis",
            "GraphQL", "REST APIs", "Microservices", "CI/CD", "Git"
        ]
        
        name = random.choice(names)
        title = random.choice(titles)
        company = random.choice(companies)
        years = random.randint(3, 12)
        skills = random.sample(skills_pool, k=random.randint(5, 10))
        
        return json.dumps({
            "name": name,
            "current_title": title,
            "current_company": company,
            "years_experience": years,
            "skills": skills,
            "location": random.choice(["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX"]),
            "education": random.choice(["BS Computer Science", "MS Software Engineering", "BS Engineering"]),
            "linkedin_url": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
            "github_url": f"https://github.com/{name.lower().replace(' ', '')}",
            "fit_score": round(random.uniform(0.7, 0.95), 2),
            "summary": f"Experienced {title} with {years} years building scalable systems."
        }, indent=2)

    def _generate_screening_evaluation(self) -> str:
        """Generate screening evaluation"""
        score = round(random.uniform(0.65, 0.95), 2)
        passed = score >= 0.75
        
        return json.dumps({
            "screening_score": score,
            "passed": passed,
            "technical_skills_score": round(random.uniform(0.7, 0.95), 2),
            "experience_score": round(random.uniform(0.6, 0.9), 2),
            "education_score": round(random.uniform(0.7, 0.95), 2),
            "cultural_fit_score": round(random.uniform(0.65, 0.9), 2),
            "strengths": [
                "Strong technical background in required technologies",
                "Relevant industry experience",
                "Good communication skills demonstrated in profile"
            ],
            "concerns": [
                "May need to verify depth of experience in specific areas"
            ] if score < 0.85 else [],
            "recommendation": "PROCEED" if passed else "REJECT",
            "notes": f"Candidate shows {'strong' if passed else 'moderate'} alignment with job requirements."
        }, indent=2)
    
    def _generate_outreach_message(self) -> str:
        """Generate personalized outreach message"""
        templates = [
            {
                "subject": "Exciting opportunity at [Company]",
                "message": "Hi [Name],\n\nI came across your profile and was impressed by your experience with [Skills]. We have an exciting opportunity for a [Role] that aligns perfectly with your background.\n\nWould you be open to a brief conversation?\n\nBest regards,\n[Recruiter]"
            },
            {
                "subject": "Your background caught our attention",
                "message": "Hello [Name],\n\nYour work at [Company] and expertise in [Skills] stood out to us. We're building something special and think you'd be a great fit.\n\nInterested in learning more?\n\nCheers,\n[Recruiter]"
            }
        ]
        
        template = random.choice(templates)
        return json.dumps({
            "channel": "email",
            "subject": template["subject"],
            "message": template["message"],
            "personalization_score": round(random.uniform(0.75, 0.95), 2),
            "tone": "professional_friendly",
            "estimated_response_rate": round(random.uniform(0.15, 0.35), 2)
        }, indent=2)
    
    def _generate_scheduling_response(self) -> str:
        """Generate interview scheduling response"""
        return json.dumps({
            "optimal_slots": [
                {"date": "2024-03-20", "time": "10:00 AM", "timezone": "PST"},
                {"date": "2024-03-21", "time": "2:00 PM", "timezone": "PST"},
                {"date": "2024-03-22", "time": "11:00 AM", "timezone": "PST"}
            ],
            "conflicts_detected": random.choice([True, False]),
            "recommended_slot": {"date": "2024-03-20", "time": "10:00 AM", "timezone": "PST"},
            "calendar_invite_ready": True
        }, indent=2)

    def _generate_hiring_recommendation(self) -> str:
        """Generate hiring recommendation"""
        score = round(random.uniform(0.7, 0.95), 2)
        
        return json.dumps({
            "overall_score": score,
            "recommendation": "STRONG_HIRE" if score >= 0.85 else "HIRE" if score >= 0.75 else "MAYBE",
            "confidence": round(random.uniform(0.75, 0.95), 2),
            "key_strengths": [
                "Exceptional technical skills",
                "Strong cultural fit",
                "Proven track record of delivery"
            ],
            "areas_for_development": [
                "Could benefit from mentorship in [specific area]"
            ] if score < 0.9 else [],
            "interview_summary": "Candidate demonstrated strong technical knowledge and problem-solving abilities.",
            "next_steps": "Proceed with offer" if score >= 0.8 else "Additional technical round recommended"
        }, indent=2)
    
    def _generate_generic_response(self, prompt: str) -> str:
        """Generate generic response for unrecognized prompts"""
        return f"Mock response for prompt: {prompt[:100]}..."
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Rough estimation: ~4 characters per token
        """
        return max(1, len(text) // 4)


# Singleton instance for easy import
mock_bedrock_client = MockBedrockClient()


def get_mock_bedrock_client(latency_ms: int = 500) -> MockBedrockClient:
    """
    Get mock Bedrock client instance
    
    Args:
        latency_ms: Simulated API latency
        
    Returns:
        MockBedrockClient instance
    """
    return MockBedrockClient(latency_ms=latency_ms)
