"""
Scheduling Agent - Coordinates interview scheduling across candidates and interviewers

Implements: 08_agent_specifications.md - Section 7 (Scheduling Agent Specification)
Architecture: 07_system_architecture.md - Section 2.3.4 (Scheduling Agent)

This agent handles:
- Availability collection and parsing
- Optimal time slot identification across timezones
- Conflict resolution
- Calendar event creation (simulated)
- Reminder scheduling
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pytz

from shared.utils import (
    invoke_bedrock,
    save_to_dynamodb,
    get_from_dynamodb,
    Config,
    generate_id,
    get_timestamp,
    format_error_response,
    format_success_response
)

logger = logging.getLogger(__name__)


@dataclass
class TimeSlot:
    """Represents a potential meeting time slot"""
    start_time: datetime
    end_time: datetime
    score: float
    timezone: str


@dataclass
class ScheduledInterview:
    """Represents a scheduled interview"""
    interview_id: str
    candidate_id: str
    interviewer_id: str
    scheduled_time: datetime
    duration_minutes: int
    timezone: str
    meeting_link: str
    calendar_event_id: str
    confirmation_sent: bool
    reminders_scheduled: List[Dict[str, Any]]


class SchedulingAgent:
    """
    Scheduling Agent coordinates interview logistics across multiple stakeholders
    
    Responsibilities:
    - Find optimal meeting times across calendars
    - Handle timezone conversions
    - Create calendar events (simulated)
    - Schedule reminders
    - Resolve scheduling conflicts
    """
    
    def __init__(self):
        self.agent_name = "scheduling_agent"
        self.model_id = Config.BEDROCK_MODEL_ID
        self.temperature = 0.1  # Very low for deterministic scheduling
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for scheduling agent
        
        Args:
            task_data: Contains candidates, interviewers, and scheduling parameters
            
        Returns:
            Dict with scheduled interviews and conflicts
        """
        try:
            logger.info(f"Scheduling Agent executing task: {task_data.get('task_id')}")
            
            # Extract task data
            task_id = task_data.get('task_id')
            job_id = task_data.get('job_id')
            candidates = task_data.get('candidates', [])
            interviewers = task_data.get('interviewers', [])
            parameters = task_data.get('scheduling_parameters', {})
            
            # Validate inputs
            if not candidates:
                return format_error_response("No candidates provided for scheduling")
            
            if not interviewers:
                return format_error_response("No interviewers provided for scheduling")
            
            # Schedule interviews for each candidate
            scheduled_interviews = []
            scheduling_conflicts = []
            
            for candidate in candidates:
                result = self._schedule_single_interview(
                    candidate=candidate,
                    interviewers=interviewers,
                    parameters=parameters,
                    job_id=job_id
                )
                
                if result['success']:
                    scheduled_interviews.append(result['interview'])
                else:
                    scheduling_conflicts.append({
                        'candidate_id': candidate['candidate_id'],
                        'issue': result['error'],
                        'suggested_action': result.get('suggestion', 'Manual intervention required')
                    })
            
            # Calculate success metrics
            total_candidates = len(candidates)
            successful_schedules = len(scheduled_interviews)
            success_rate = successful_schedules / total_candidates if total_candidates > 0 else 0
            
            # Save scheduled interviews to DynamoDB
            for interview in scheduled_interviews:
                self._save_interview(interview, job_id)
            
            # Generate summary
            summary = {
                'success_rate': round(success_rate, 2),
                'interviews_scheduled': successful_schedules,
                'conflicts': len(scheduling_conflicts),
                'average_time_to_schedule': self._calculate_avg_schedule_time(scheduled_interviews)
            }
            
            # Prepare response
            response = {
                'status': 'success',
                'interviews_scheduled': successful_schedules,
                'scheduled_interviews': [self._interview_to_dict(i) for i in scheduled_interviews],
                'scheduling_conflicts': scheduling_conflicts,
                'scheduling_summary': summary,
                'confidence': self._calculate_confidence(success_rate),
                'reasoning': self._generate_reasoning(successful_schedules, total_candidates, scheduling_conflicts),
                'next_agent': 'evaluation',
                'metadata': {
                    'execution_time': '5s',
                    'agent': self.agent_name,
                    'timestamp': get_timestamp()
                }
            }
            
            logger.info(f"Scheduling completed: {successful_schedules}/{total_candidates} interviews scheduled")
            return response
            
        except Exception as e:
            logger.error(f"Scheduling Agent error: {str(e)}")
            return format_error_response(f"Scheduling failed: {str(e)}")

    
    def _schedule_single_interview(
        self,
        candidate: Dict[str, Any],
        interviewers: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        job_id: str
    ) -> Dict[str, Any]:
        """
        Schedule interview for a single candidate
        
        Args:
            candidate: Candidate data with availability
            interviewers: List of available interviewers
            parameters: Scheduling parameters
            job_id: Job ID
            
        Returns:
            Dict with success status and interview or error
        """
        try:
            candidate_id = candidate['candidate_id']
            
            # Parse availability
            candidate_availability = self._parse_availability(
                candidate.get('availability', {}),
                candidate.get('timezone', 'America/Los_Angeles')
            )
            
            # Get interviewer availability (simulated for hackathon)
            interviewer_availability = self._get_interviewer_availability(
                interviewers,
                parameters.get('buffer_days', 3)
            )
            
            # Find optimal slot
            optimal_slot = self._find_optimal_slot(
                candidate_availability,
                interviewer_availability,
                candidate.get('availability', {}).get('blackout_dates', []),
                parameters
            )
            
            if not optimal_slot:
                return {
                    'success': False,
                    'error': 'No overlapping availability found',
                    'suggestion': 'Request additional availability from candidate'
                }
            
            # Select interviewer (first available for simplicity)
            interviewer = interviewers[0]
            
            # Create interview record
            interview = ScheduledInterview(
                interview_id=generate_id('INT'),
                candidate_id=candidate_id,
                interviewer_id=interviewer['interviewer_id'],
                scheduled_time=optimal_slot.start_time,
                duration_minutes=parameters.get('interview_duration', 60),
                timezone=candidate.get('timezone', 'America/Los_Angeles'),
                meeting_link=self._generate_meeting_link(),
                calendar_event_id=generate_id('cal_event_'),
                confirmation_sent=True,
                reminders_scheduled=self._schedule_reminders(
                    optimal_slot.start_time,
                    parameters.get('reminder_hours', [24, 2])
                )
            )
            
            # Send confirmation (simulated)
            self._send_confirmation(candidate, interviewer, interview)
            
            return {
                'success': True,
                'interview': interview
            }
            
        except Exception as e:
            logger.error(f"Error scheduling interview for {candidate.get('candidate_id')}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'suggestion': 'Manual scheduling required'
            }
    
    def _parse_availability(
        self,
        availability: Dict[str, Any],
        timezone: str
    ) -> List[TimeSlot]:
        """
        Parse candidate availability into time slots
        
        Args:
            availability: Availability data with preferred days/times
            timezone: Candidate timezone
            
        Returns:
            List of available time slots
        """
        slots = []
        tz = pytz.timezone(timezone)
        
        preferred_days = availability.get('preferred_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        preferred_times = availability.get('preferred_times', ['10:00-12:00', '14:00-16:00'])
        
        # Generate slots for next 14 days
        start_date = datetime.now(tz).date() + timedelta(days=3)  # Buffer of 3 days
        
        for day_offset in range(14):
            current_date = start_date + timedelta(days=day_offset)
            day_name = current_date.strftime('%A')
            
            if day_name in preferred_days:
                for time_range in preferred_times:
                    start_time_str, end_time_str = time_range.split('-')
                    
                    # Parse time
                    start_hour, start_min = map(int, start_time_str.split(':'))
                    end_hour, end_min = map(int, end_time_str.split(':'))
                    
                    # Create datetime objects
                    start_dt = tz.localize(datetime.combine(
                        current_date,
                        datetime.min.time().replace(hour=start_hour, minute=start_min)
                    ))
                    end_dt = tz.localize(datetime.combine(
                        current_date,
                        datetime.min.time().replace(hour=end_hour, minute=end_min)
                    ))
                    
                    slots.append(TimeSlot(
                        start_time=start_dt,
                        end_time=end_dt,
                        score=0.0,
                        timezone=timezone
                    ))
        
        return slots
    
    def _get_interviewer_availability(
        self,
        interviewers: List[Dict[str, Any]],
        buffer_days: int
    ) -> List[TimeSlot]:
        """
        Get interviewer availability (simulated for hackathon)
        
        In production, this would call calendar APIs.
        For demo, we generate reasonable availability.
        
        Args:
            interviewers: List of interviewers
            buffer_days: Days to buffer before scheduling
            
        Returns:
            List of available time slots
        """
        slots = []
        
        # Simulate interviewer availability (9am-5pm, weekdays)
        # In production: fetch from Google Calendar / Outlook API
        interviewer_tz = pytz.timezone(interviewers[0].get('timezone', 'America/New_York'))
        start_date = datetime.now(interviewer_tz).date() + timedelta(days=buffer_days)
        
        for day_offset in range(14):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Generate 9am-5pm availability in 1-hour blocks
            for hour in range(9, 17):
                start_dt = interviewer_tz.localize(datetime.combine(
                    current_date,
                    datetime.min.time().replace(hour=hour, minute=0)
                ))
                end_dt = start_dt + timedelta(hours=1)
                
                slots.append(TimeSlot(
                    start_time=start_dt,
                    end_time=end_dt,
                    score=0.0,
                    timezone=interviewers[0].get('timezone', 'America/New_York')
                ))
        
        return slots

    
    def _find_optimal_slot(
        self,
        candidate_slots: List[TimeSlot],
        interviewer_slots: List[TimeSlot],
        blackout_dates: List[str],
        parameters: Dict[str, Any]
    ) -> Optional[TimeSlot]:
        """
        Find optimal meeting slot considering all constraints
        
        Algorithm:
        1. Find overlapping time slots
        2. Remove blackout dates
        3. Score slots (prefer earlier dates, mid-day times, avoid Mon/Fri)
        4. Return highest scored slot
        
        Args:
            candidate_slots: Candidate available slots
            interviewer_slots: Interviewer available slots
            blackout_dates: Dates to avoid (ISO format)
            parameters: Scheduling parameters
            
        Returns:
            Optimal TimeSlot or None if no overlap
        """
        # Convert blackout dates to date objects
        blackout_date_objs = []
        for date_str in blackout_dates:
            try:
                blackout_date_objs.append(datetime.fromisoformat(date_str).date())
            except:
                logger.warning(f"Invalid blackout date format: {date_str}")
        
        # Find overlapping slots (convert to UTC for comparison)
        overlapping_slots = []
        
        for c_slot in candidate_slots:
            c_start_utc = c_slot.start_time.astimezone(pytz.UTC)
            c_end_utc = c_slot.end_time.astimezone(pytz.UTC)
            
            for i_slot in interviewer_slots:
                i_start_utc = i_slot.start_time.astimezone(pytz.UTC)
                i_end_utc = i_slot.end_time.astimezone(pytz.UTC)
                
                # Check for overlap (at least 1 hour)
                overlap_start = max(c_start_utc, i_start_utc)
                overlap_end = min(c_end_utc, i_end_utc)
                
                if overlap_end > overlap_start:
                    duration = (overlap_end - overlap_start).total_seconds() / 3600
                    
                    if duration >= 1.0:  # At least 1 hour overlap
                        # Use candidate's timezone for the slot
                        overlapping_slots.append(TimeSlot(
                            start_time=overlap_start.astimezone(pytz.timezone(c_slot.timezone)),
                            end_time=overlap_start.astimezone(pytz.timezone(c_slot.timezone)) + timedelta(hours=1),
                            score=0.0,
                            timezone=c_slot.timezone
                        ))
        
        if not overlapping_slots:
            return None
        
        # Remove blackout dates
        filtered_slots = [
            slot for slot in overlapping_slots
            if slot.start_time.date() not in blackout_date_objs
        ]
        
        if not filtered_slots:
            return None
        
        # Score slots
        scored_slots = []
        now = datetime.now(pytz.UTC)
        
        for slot in filtered_slots:
            score = 0.0
            
            # Prefer earlier dates (within 2 weeks)
            days_out = (slot.start_time.date() - now.date()).days
            if days_out <= 14:
                score += max(0, 1.0 - (days_out / 14))
            
            # Prefer mid-day times (10am-3pm)
            hour = slot.start_time.hour
            if 10 <= hour <= 15:
                score += 0.5
            
            # Avoid Mondays (0) and Fridays (4)
            weekday = slot.start_time.weekday()
            if weekday not in [0, 4]:
                score += 0.3
            
            # Prefer Tuesday-Thursday
            if weekday in [1, 2, 3]:
                score += 0.2
            
            scored_slots.append((slot, score))
        
        # Return highest scored slot
        best_slot, best_score = max(scored_slots, key=lambda x: x[1])
        best_slot.score = best_score
        
        logger.info(f"Found optimal slot: {best_slot.start_time.isoformat()} (score: {best_score:.2f})")
        return best_slot
    
    def _generate_meeting_link(self) -> str:
        """
        Generate meeting link (simulated for hackathon)
        
        In production: Call Zoom/Teams API to create meeting
        """
        meeting_id = generate_id('')[:10]
        return f"https://zoom.us/j/{meeting_id}"
    
    def _schedule_reminders(
        self,
        interview_time: datetime,
        reminder_hours: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Schedule reminders before interview
        
        Args:
            interview_time: Scheduled interview time
            reminder_hours: Hours before interview to send reminders
            
        Returns:
            List of scheduled reminders
        """
        reminders = []
        
        for hours in reminder_hours:
            reminder_time = interview_time - timedelta(hours=hours)
            reminders.append({
                'time': reminder_time.isoformat(),
                'type': f'{hours}h_reminder',
                'status': 'scheduled'
            })
        
        return reminders
    
    def _send_confirmation(
        self,
        candidate: Dict[str, Any],
        interviewer: Dict[str, Any],
        interview: ScheduledInterview
    ) -> None:
        """
        Send confirmation emails (simulated for hackathon)
        
        In production: Use Amazon SES or similar email service
        """
        logger.info(f"Sending confirmation to {candidate['email']} and {interviewer['email']}")
        
        # Simulated email sending
        # In production: Call SES API
        confirmation_data = {
            'to': [candidate['email'], interviewer['email']],
            'subject': f"Interview Scheduled - {interview.scheduled_time.strftime('%B %d, %Y at %I:%M %p')}",
            'body': f"""
Interview scheduled successfully!

Candidate: {candidate['name']}
Interviewer: {interviewer['name']}
Time: {interview.scheduled_time.strftime('%B %d, %Y at %I:%M %p %Z')}
Duration: {interview.duration_minutes} minutes
Meeting Link: {interview.meeting_link}

You will receive reminders 24 hours and 2 hours before the interview.
            """.strip()
        }
        
        logger.info(f"Confirmation sent: {confirmation_data['subject']}")
    
    def _save_interview(self, interview: ScheduledInterview, job_id: str) -> None:
        """
        Save scheduled interview to DynamoDB
        
        Args:
            interview: Scheduled interview data
            job_id: Job ID
        """
        interview_data = {
            'interviewId': interview.interview_id,
            'candidateId': interview.candidate_id,
            'interviewerId': interview.interviewer_id,
            'jobId': job_id,
            'scheduledTime': interview.scheduled_time.isoformat(),
            'durationMinutes': interview.duration_minutes,
            'timezone': interview.timezone,
            'meetingLink': interview.meeting_link,
            'calendarEventId': interview.calendar_event_id,
            'confirmationSent': interview.confirmation_sent,
            'remindersScheduled': interview.reminders_scheduled,
            'status': 'scheduled',
            'createdAt': get_timestamp()
        }
        
        save_to_dynamodb(Config.INTERACTIONS_TABLE, interview_data)
        logger.info(f"Saved interview {interview.interview_id} to DynamoDB")
    
    def _interview_to_dict(self, interview: ScheduledInterview) -> Dict[str, Any]:
        """Convert ScheduledInterview to dictionary"""
        return {
            'interview_id': interview.interview_id,
            'candidate_id': interview.candidate_id,
            'interviewer_id': interview.interviewer_id,
            'scheduled_time': interview.scheduled_time.isoformat(),
            'duration_minutes': interview.duration_minutes,
            'timezone': interview.timezone,
            'meeting_link': interview.meeting_link,
            'calendar_event_id': interview.calendar_event_id,
            'confirmation_sent': interview.confirmation_sent,
            'reminders_scheduled': interview.reminders_scheduled
        }
    
    def _calculate_avg_schedule_time(self, interviews: List[ScheduledInterview]) -> str:
        """Calculate average time from now to scheduled interviews"""
        if not interviews:
            return "N/A"
        
        now = datetime.now(pytz.UTC)
        total_days = sum(
            (interview.scheduled_time.astimezone(pytz.UTC) - now).days
            for interview in interviews
        )
        avg_days = total_days / len(interviews)
        
        return f"{avg_days:.1f} days"
    
    def _calculate_confidence(self, success_rate: float) -> float:
        """Calculate confidence score based on success rate"""
        # High confidence if most interviews scheduled successfully
        if success_rate >= 0.9:
            return 0.95
        elif success_rate >= 0.75:
            return 0.85
        elif success_rate >= 0.5:
            return 0.70
        else:
            return 0.50
    
    def _generate_reasoning(
        self,
        successful: int,
        total: int,
        conflicts: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable reasoning for scheduling results"""
        if successful == total:
            return f"Successfully scheduled all {total} interviews with optimal time slots."
        elif successful == 0:
            return f"Unable to schedule any interviews. All {total} candidates had conflicts."
        else:
            conflict_summary = f"{len(conflicts)} conflict(s)" if conflicts else "some conflicts"
            return f"Successfully scheduled {successful} of {total} interviews. {conflict_summary} require manual intervention."


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Scheduling Agent
    
    Args:
        event: Lambda event containing task data
        context: Lambda context
        
    Returns:
        Scheduling results
    """
    agent = SchedulingAgent()
    return agent.execute(event)
