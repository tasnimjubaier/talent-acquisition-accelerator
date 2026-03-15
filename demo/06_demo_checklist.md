# Demo Preparation Checklist

**Purpose:** Ensure system is ready for demo video recording  
**Status:** Pre-Demo Validation

---

## System Validation

### Infrastructure
- [ ] AWS credentials configured and valid
- [ ] DynamoDB tables accessible
- [ ] Lambda functions deployed
- [ ] API Gateway endpoints responding
- [ ] Bedrock/Nova access confirmed
- [ ] CloudWatch logs capturing events

### Agent Functionality
- [ ] Sourcing Agent finds candidates successfully
- [ ] Screening Agent evaluates candidates correctly
- [ ] Outreach Agent generates personalized messages
- [ ] Scheduling Agent proposes valid times
- [ ] Evaluation Agent produces comprehensive reports
- [ ] Supervisor Agent coordinates all agents

### Demo Scenarios
- [ ] Scenario 1 (Happy Path) runs successfully
- [ ] Scenario 2 (High Volume) completes in < 30s
- [ ] Scenario 3 (Edge Cases) handles intelligently
- [ ] All scenarios tested 5 times with 100% success rate
- [ ] Performance metrics within targets
- [ ] Cost per scenario < $0.50

---

## Demo Data Validation

### Sample Jobs
- [ ] Job descriptions realistic and complete
- [ ] Required skills clearly defined
- [ ] Job IDs match scenario references

### Sample Candidates
- [ ] Candidate profiles diverse and realistic
- [ ] Skills and experience varied
- [ ] Edge case candidates included
- [ ] Contact information uses placeholders
- [ ] No real PII included

### Expected Outcomes
- [ ] Expected scores documented
- [ ] Success criteria defined
- [ ] Validation logic implemented


---

## Recording Environment

### Technical Setup
- [ ] Screen recording software tested
- [ ] Audio recording equipment working
- [ ] Microphone quality verified
- [ ] Screen resolution set to 1080p minimum
- [ ] Browser/terminal windows sized appropriately
- [ ] Demo environment clean (no test data visible)

### Visual Preparation
- [ ] Architecture diagrams exported
- [ ] Code snippets prepared
- [ ] GitHub repository public and clean
- [ ] README.md complete and professional
- [ ] No sensitive information visible

### Script Preparation
- [ ] Demo script reviewed and practiced
- [ ] Timing validated (< 3 minutes)
- [ ] Key talking points memorized
- [ ] Backup talking points ready
- [ ] #AmazonNova hashtag placement confirmed

---

## Performance Validation

### Execution Metrics
- [ ] End-to-end pipeline < 60 seconds
- [ ] Sourcing stage < 15 seconds
- [ ] Screening stage < 20 seconds
- [ ] Outreach stage < 10 seconds
- [ ] Scheduling stage < 10 seconds
- [ ] Evaluation stage < 15 seconds

### Cost Metrics
- [ ] Total cost per job < $0.50
- [ ] Token usage < 100K per job
- [ ] No unexpected AWS charges
- [ ] Cost tracking accurate

### Quality Metrics
- [ ] Candidate match scores > 0.60
- [ ] Screening accuracy > 80%
- [ ] Outreach messages personalized
- [ ] Evaluation reasoning clear and detailed

---

## Demo Execution

### Pre-Recording
- [ ] Run demo scenarios one final time
- [ ] Clear all logs and test data
- [ ] Restart services if needed
- [ ] Close unnecessary applications
- [ ] Disable notifications
- [ ] Set "Do Not Disturb" mode

### During Recording
- [ ] Speak clearly and confidently
- [ ] Follow script timing
- [ ] Show key features prominently
- [ ] Highlight Amazon Nova usage
- [ ] Demonstrate real outputs (not mocked)
- [ ] Keep energy high and engaging

### Post-Recording
- [ ] Review recording for errors
- [ ] Check audio quality
- [ ] Verify video length < 3 minutes
- [ ] Confirm all key points covered
- [ ] Edit for smooth transitions
- [ ] Add text overlays if needed
