"""
Agents Package

This package contains all agent implementations for the Talent Acquisition Accelerator:
- SupervisorAgent: Orchestrates the multi-agent workflow
- SourcingAgent: Finds and qualifies candidates (Phase 4)
- ScreeningAgent: Evaluates candidates against requirements (Phase 4)
- OutreachAgent: Engages candidates with personalized messages (Phase 4)
- SchedulingAgent: Coordinates interview scheduling (Phase 4)
- EvaluationAgent: Synthesizes feedback and provides recommendations (Phase 4)

References:
- 07_system_architecture.md: Agent architecture and coordination
- 08_agent_specifications.md: Detailed agent requirements
"""

from agents.supervisor_agent import SupervisorAgent
from agents.sourcing_agent import SourcingAgent
from agents.screening_agent import ScreeningAgent
from agents.outreach_agent import OutreachAgent

__all__ = [
    'SupervisorAgent',
    'SourcingAgent',
    'ScreeningAgent',
    'OutreachAgent'
]

__version__ = '0.1.0'
