"""
Unit tests for Scheduling Agent

Tests:
- Availability parsing
- Slot optimization algorithm
- Timezone handling
- Conflict resolution
- Interview scheduling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.scheduling_agent import SchedulingAgent, TimeSlot, ScheduledInterview


@pytest.fixture
def scheduling_agent():
    """Create SchedulingAgent instance for testing"""
    return SchedulingAgent()


@pytest.fixture
def sample_candidate():
    """Sample candidate data"""
    return {
        'candidate_id': 'C001',
        'name': 'John Doe',
        'email': 'john@example.com',
        'timezone': 'America/Los_Angeles',
        'availability': {
            'preferred_days': ['Monday', 'Tuesday', 'Wednesday'],
            'preferred_times': ['10:00-12:00', '14:00-16:00'],
            'blackout_dates': []
        }
    }


@pytest.fixture
def sample_interviewers():
    """Sample interviewer data"""
    return [
        {
            'interviewer_id': 'I001',
            'name': 'Jane Smith',
            'email': 'jane@techcorp.com',
            'role': 'Senior Engineer',
            'timezone': 'America/New_York'
        }
    ]


@pytest.fixture
def sample_parameters():
    """Sample scheduling parameters"""
    return {
        'buffer_days': 3,
        'interview_duration': 60,
        'max_attempts': 3,
        'meeting_platform': 'zoom',
        'send_reminders': True,
        'reminder_hours': [24, 2]
    }


class TestAvailabilityParsing:
    """Test availability parsing functionality"""
    
    def test_parse_availability_basic(self, scheduling_agent, sample_candidate):
        """Test basic availability parsing"""
        availability = sample_candidate['availability']
        timezone = sample_candidate['timezone']
        
        slots = scheduling_agent._parse_availability(availability, timezone)
        
        assert len(slots) > 0
        assert all(isinstance(slot, TimeSlot) for slot in slots)
        assert all(slot.timezone == timezone for slot in slots)
    
    def test_parse_availability_respects_preferred_days(self, scheduling_agent):
        """Test that only preferred days are included"""
        availability = {
            'preferred_days': ['Monday'],
            'preferred_times': ['10:00-12:00']
        }
        
        slots = scheduling_agent._parse_availability(availability, 'America/Los_Angeles')
        
        # All slots should be on Monday
        assert all(slot.start_time.strftime('%A') == 'Monday' for slot in slots)
    
    def test_parse_availability_time_ranges(self, scheduling_agent):
        """Test that time ranges are parsed correctly"""
        availability = {
            'preferred_days': ['Monday', 'Tuesday'],
            'preferred_times': ['09:00-11:00', '14:00-16:00']
        }
        
        slots = scheduling_agent._parse_availability(availability, 'America/Los_Angeles')
        
        # Should have slots for both time ranges
        morning_slots = [s for s in slots if 9 <= s.start_time.hour < 11]
        afternoon_slots = [s for s in slots if 14 <= s.start_time.hour < 16]
        
        assert len(morning_slots) > 0
        assert len(afternoon_slots) > 0


class TestSlotOptimization:
    """Test slot optimization algorithm"""
    
    def test_find_optimal_slot_with_overlap(self, scheduling_agent):
        """Test finding optimal slot when overlap exists"""
        tz_la = pytz.timezone('America/Los_Angeles')
        base_date = datetime.now(tz_la).date() + timedelta(days=5)
        
        # Candidate available 10am-12pm
        candidate_slots = [
            TimeSlot(
                start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=10))),
                end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=12))),
                score=0.0,
                timezone='America/Los_Angeles'
            )
        ]
        
        # Interviewer available 10am-2pm (converted to LA time)
        tz_ny = pytz.timezone('America/New_York')
        interviewer_slots = [
            TimeSlot(
                start_time=tz_ny.localize(datetime.combine(base_date, datetime.min.time().replace(hour=13))),  # 10am LA
                end_time=tz_ny.localize(datetime.combine(base_date, datetime.min.time().replace(hour=17))),  # 2pm LA
                score=0.0,
                timezone='America/New_York'
            )
        ]
        
        optimal_slot = scheduling_agent._find_optimal_slot(
            candidate_slots,
            interviewer_slots,
            [],
            {}
        )
        
        assert optimal_slot is not None
        assert optimal_slot.timezone == 'America/Los_Angeles'
    
    def test_find_optimal_slot_no_overlap(self, scheduling_agent):
        """Test when no overlap exists"""
        tz_la = pytz.timezone('America/Los_Angeles')
        base_date = datetime.now(tz_la).date() + timedelta(days=5)
        
        # Candidate available 10am-12pm
        candidate_slots = [
            TimeSlot(
                start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=10))),
                end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=12))),
                score=0.0,
                timezone='America/Los_Angeles'
            )
        ]
        
        # Interviewer available 2pm-4pm (no overlap)
        interviewer_slots = [
            TimeSlot(
                start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=14))),
                end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=16))),
                score=0.0,
                timezone='America/Los_Angeles'
            )
        ]
        
        optimal_slot = scheduling_agent._find_optimal_slot(
            candidate_slots,
            interviewer_slots,
            [],
            {}
        )
        
        assert optimal_slot is None
    
    def test_find_optimal_slot_respects_blackout_dates(self, scheduling_agent):
        """Test that blackout dates are excluded"""
        tz_la = pytz.timezone('America/Los_Angeles')
        base_date = datetime.now(tz_la).date() + timedelta(days=5)
        
        candidate_slots = [
            TimeSlot(
                start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=10))),
                end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=12))),
                score=0.0,
                timezone='America/Los_Angeles'
            )
        ]
        
        interviewer_slots = [
            TimeSlot(
                start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=10))),
                end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=12))),
                score=0.0,
                timezone='America/Los_Angeles'
            )
        ]
        
        # Blackout the date
        blackout_dates = [base_date.isoformat()]
        
        optimal_slot = scheduling_agent._find_optimal_slot(
            candidate_slots,
            interviewer_slots,
            blackout_dates,
            {}
        )
        
        assert optimal_slot is None
    
    def test_slot_scoring_prefers_midday(self, scheduling_agent):
        """Test that mid-day times get higher scores"""
        tz_la = pytz.timezone('America/Los_Angeles')
        base_date = datetime.now(tz_la).date() + timedelta(days=5)
        
        # Create slots at different times
        morning_slot = TimeSlot(
            start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=8))),
            end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=9))),
            score=0.0,
            timezone='America/Los_Angeles'
        )
        
        midday_slot = TimeSlot(
            start_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=11))),
            end_time=tz_la.localize(datetime.combine(base_date, datetime.min.time().replace(hour=12))),
            score=0.0,
            timezone='America/Los_Angeles'
        )
        
        candidate_slots = [morning_slot, midday_slot]
        interviewer_slots = [morning_slot, midday_slot]
        
        optimal_slot = scheduling_agent._find_optimal_slot(
            candidate_slots,
            interviewer_slots,
            [],
            {}
        )
        
        # Should prefer midday slot
        assert optimal_slot.start_time.hour == 11


class TestInterviewScheduling:
    """Test interview scheduling functionality"""
    
    @patch('agents.scheduling_agent.save_to_dynamodb')
    def test_schedule_single_interview_success(
        self,
        mock_save,
        scheduling_agent,
        sample_candidate,
        sample_interviewers,
        sample_parameters
    ):
        """Test successful single interview scheduling"""
        result = scheduling_agent._schedule_single_interview(
            candidate=sample_candidate,
            interviewers=sample_interviewers,
            parameters=sample_parameters,
            job_id='JOB001'
        )
        
        assert result['success'] is True
        assert 'interview' in result
        
        interview = result['interview']
        assert isinstance(interview, ScheduledInterview)
        assert interview.candidate_id == 'C001'
        assert interview.interviewer_id == 'I001'
        assert interview.duration_minutes == 60
        assert len(interview.reminders_scheduled) == 2

    
    def test_schedule_single_interview_no_availability(
        self,
        scheduling_agent,
        sample_interviewers,
        sample_parameters
    ):
        """Test scheduling when no availability overlap"""
        # Candidate with very limited availability
        limited_candidate = {
            'candidate_id': 'C002',
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'timezone': 'America/Los_Angeles',
            'availability': {
                'preferred_days': [],  # No preferred days
                'preferred_times': [],
                'blackout_dates': []
            }
        }
        
        result = scheduling_agent._schedule_single_interview(
            candidate=limited_candidate,
            interviewers=sample_interviewers,
            parameters=sample_parameters,
            job_id='JOB001'
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert 'suggestion' in result


class TestReminderScheduling:
    """Test reminder scheduling functionality"""
    
    def test_schedule_reminders(self, scheduling_agent):
        """Test reminder scheduling"""
        interview_time = datetime.now(pytz.UTC) + timedelta(days=5)
        reminder_hours = [24, 2]
        
        reminders = scheduling_agent._schedule_reminders(interview_time, reminder_hours)
        
        assert len(reminders) == 2
        assert reminders[0]['type'] == '24h_reminder'
        assert reminders[1]['type'] == '2h_reminder'
        assert all('time' in r for r in reminders)
        assert all('status' in r for r in reminders)
    
    def test_reminder_times_correct(self, scheduling_agent):
        """Test that reminder times are calculated correctly"""
        interview_time = datetime(2026, 3, 20, 14, 0, 0, tzinfo=pytz.UTC)
        reminder_hours = [24]
        
        reminders = scheduling_agent._schedule_reminders(interview_time, reminder_hours)
        
        reminder_time = datetime.fromisoformat(reminders[0]['time'])
        expected_time = interview_time - timedelta(hours=24)
        
        assert reminder_time == expected_time


class TestHelperMethods:
    """Test helper methods"""
    
    def test_generate_meeting_link(self, scheduling_agent):
        """Test meeting link generation"""
        link = scheduling_agent._generate_meeting_link()
        
        assert link.startswith('https://zoom.us/j/')
        assert len(link) > 20
    
    def test_calculate_confidence(self, scheduling_agent):
        """Test confidence calculation"""
        assert scheduling_agent._calculate_confidence(1.0) == 0.95
        assert scheduling_agent._calculate_confidence(0.9) == 0.95
        assert scheduling_agent._calculate_confidence(0.8) == 0.85
        assert scheduling_agent._calculate_confidence(0.6) == 0.70
        assert scheduling_agent._calculate_confidence(0.3) == 0.50
    
    def test_generate_reasoning(self, scheduling_agent):
        """Test reasoning generation"""
        # All successful
        reasoning = scheduling_agent._generate_reasoning(5, 5, [])
        assert "all 5 interviews" in reasoning.lower()
        
        # Partial success
        conflicts = [{'candidate_id': 'C001', 'issue': 'No overlap'}]
        reasoning = scheduling_agent._generate_reasoning(4, 5, conflicts)
        assert "4 of 5" in reasoning
        
        # All failed
        reasoning = scheduling_agent._generate_reasoning(0, 5, conflicts)
        assert "unable" in reasoning.lower()
    
    def test_interview_to_dict(self, scheduling_agent):
        """Test interview conversion to dictionary"""
        interview = ScheduledInterview(
            interview_id='INT001',
            candidate_id='C001',
            interviewer_id='I001',
            scheduled_time=datetime.now(pytz.UTC),
            duration_minutes=60,
            timezone='America/Los_Angeles',
            meeting_link='https://zoom.us/j/123',
            calendar_event_id='cal_123',
            confirmation_sent=True,
            reminders_scheduled=[]
        )
        
        result = scheduling_agent._interview_to_dict(interview)
        
        assert result['interview_id'] == 'INT001'
        assert result['candidate_id'] == 'C001'
        assert result['interviewer_id'] == 'I001'
        assert result['duration_minutes'] == 60
        assert result['confirmation_sent'] is True


class TestFullExecution:
    """Test full agent execution"""
    
    @patch('agents.scheduling_agent.save_to_dynamodb')
    def test_execute_success(self, mock_save, scheduling_agent):
        """Test full execution with successful scheduling"""
        task_data = {
            'task_id': 'schedule_001',
            'job_id': 'JOB001',
            'candidates': [
                {
                    'candidate_id': 'C001',
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'timezone': 'America/Los_Angeles',
                    'availability': {
                        'preferred_days': ['Monday', 'Tuesday', 'Wednesday'],
                        'preferred_times': ['10:00-12:00', '14:00-16:00'],
                        'blackout_dates': []
                    }
                },
                {
                    'candidate_id': 'C002',
                    'name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'timezone': 'America/New_York',
                    'availability': {
                        'preferred_days': ['Tuesday', 'Wednesday', 'Thursday'],
                        'preferred_times': ['09:00-11:00', '13:00-15:00'],
                        'blackout_dates': []
                    }
                }
            ],
            'interviewers': [
                {
                    'interviewer_id': 'I001',
                    'name': 'Bob Johnson',
                    'email': 'bob@techcorp.com',
                    'role': 'Senior Engineer',
                    'timezone': 'America/New_York'
                }
            ],
            'scheduling_parameters': {
                'buffer_days': 3,
                'interview_duration': 60,
                'reminder_hours': [24, 2]
            }
        }
        
        result = scheduling_agent.execute(task_data)
        
        assert result['status'] == 'success'
        assert result['interviews_scheduled'] >= 0
        assert 'scheduled_interviews' in result
        assert 'scheduling_conflicts' in result
        assert 'scheduling_summary' in result
        assert 'confidence' in result
        assert 'reasoning' in result
        assert result['next_agent'] == 'evaluation'
    
    def test_execute_no_candidates(self, scheduling_agent):
        """Test execution with no candidates"""
        task_data = {
            'task_id': 'schedule_002',
            'job_id': 'JOB001',
            'candidates': [],
            'interviewers': [
                {
                    'interviewer_id': 'I001',
                    'name': 'Bob Johnson',
                    'email': 'bob@techcorp.com'
                }
            ],
            'scheduling_parameters': {}
        }
        
        result = scheduling_agent.execute(task_data)
        
        assert result['status'] == 'error'
        assert 'No candidates' in result['error']
    
    def test_execute_no_interviewers(self, scheduling_agent):
        """Test execution with no interviewers"""
        task_data = {
            'task_id': 'schedule_003',
            'job_id': 'JOB001',
            'candidates': [
                {
                    'candidate_id': 'C001',
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'timezone': 'America/Los_Angeles',
                    'availability': {}
                }
            ],
            'interviewers': [],
            'scheduling_parameters': {}
        }
        
        result = scheduling_agent.execute(task_data)
        
        assert result['status'] == 'error'
        assert 'No interviewers' in result['error']


class TestTimezoneHandling:
    """Test timezone handling"""
    
    def test_timezone_conversion_la_to_ny(self, scheduling_agent):
        """Test LA to NY timezone conversion"""
        tz_la = pytz.timezone('America/Los_Angeles')
        tz_ny = pytz.timezone('America/New_York')
        
        # 10am LA time
        la_time = tz_la.localize(datetime(2026, 3, 20, 10, 0, 0))
        
        # Convert to NY time (should be 1pm)
        ny_time = la_time.astimezone(tz_ny)
        
        assert ny_time.hour == 13  # 1pm
    
    def test_availability_parsing_different_timezones(self, scheduling_agent):
        """Test availability parsing with different timezones"""
        availability = {
            'preferred_days': ['Monday'],
            'preferred_times': ['10:00-12:00']
        }
        
        # Parse for LA timezone
        la_slots = scheduling_agent._parse_availability(availability, 'America/Los_Angeles')
        
        # Parse for NY timezone
        ny_slots = scheduling_agent._parse_availability(availability, 'America/New_York')
        
        # Both should have slots
        assert len(la_slots) > 0
        assert len(ny_slots) > 0
        
        # Times should be different when converted to UTC
        la_utc = la_slots[0].start_time.astimezone(pytz.UTC)
        ny_utc = ny_slots[0].start_time.astimezone(pytz.UTC)
        
        assert la_utc != ny_utc


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
