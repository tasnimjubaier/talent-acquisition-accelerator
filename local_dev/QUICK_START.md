# Quick Start - Local Development

Run the complete talent acquisition workflow locally in under 2 minutes.

## Prerequisites

```bash
# Ensure you're in the project root
cd talent-acquisition-accelerator

# Install dependencies (if not already done)
pip install -r requirements.txt
```

## Run Your First Workflow

### Option 1: Basic Run (Recommended)

```bash
python local_dev/local_runner.py \
  --job-file demo/01_sample_jobs.json \
  --job-index 0
```

**Expected output:**
- Workflow starts and executes all 5 agents
- Real-time progress logs
- Completion summary with metrics
- Results saved to `local_dev/results_YYYYMMDD_HHMMSS.json`

**Expected time:** 10-25 seconds  
**Expected cost (simulated):** $0.02-$0.05

### Option 2: Step-by-Step (For Learning)

```bash
python local_dev/local_runner.py \
  --job-file demo/01_sample_jobs.json \
  --job-index 0 \
  --step-by-step
```

This pauses after each agent so you can review the output.

### Option 3: Test Scenarios

```bash
# Software Engineer (high volume)
python local_dev/local_runner.py \
  --job-file local_dev/test_scenarios.json \
  --job-index 0

# Data Scientist (specialized)
python local_dev/local_runner.py \
  --job-file local_dev/test_scenarios.json \
  --job-index 1

# Product Manager (leadership)
python local_dev/local_runner.py \
  --job-file local_dev/test_scenarios.json \
  --job-index 2
```

## What to Expect

### Console Output

```
================================================================================
STARTING LOCAL WORKFLOW EXECUTION
================================================================================
Job created: job-xxx - Senior Software Engineer

================================================================================
STEP 1: Starting Workflow (Supervisor Agent)
================================================================================
Workflow started with state ID: state-xxx
Execution time: 0.52s

================================================================================
STEP 2: Candidate Sourcing
================================================================================
✓ sourcing-agent completed successfully
Execution time: 2.34s

... (continues for all 5 agents)

================================================================================
WORKFLOW SUMMARY
================================================================================

Workflow Status: completed
Agents Executed: 5/5
Total Candidates: 47

--- Cost Summary ---
Total Cost: $0.0234
Input Tokens: 1,250
Output Tokens: 890

--- Execution Times ---
supervisor-agent: 0.52s
sourcing-agent: 2.34s
screening-agent: 3.12s
outreach-agent: 1.89s
scheduling-agent: 1.45s
evaluation-agent: 2.01s

--- Top 5 Candidates ---
1. Sarah Chen - Score: 0.92 - Status: screened
2. Michael Rodriguez - Score: 0.89 - Status: screened
3. Priya Patel - Score: 0.87 - Status: screened
4. James Wilson - Score: 0.85 - Status: screened
5. Emily Thompson - Score: 0.83 - Status: screened

================================================================================

Results saved to: local_dev/results_20260315_143022.json
```

### Results File

Check the generated JSON file for complete results:

```bash
# View results
cat local_dev/results_*.json | jq .

# Or open in editor
code local_dev/results_*.json
```

## Validation Checklist

After running, verify:

- ✅ Workflow completes without errors
- ✅ All 5 agents execute (Sourcing, Screening, Outreach, Scheduling, Evaluation)
- ✅ Candidates are generated (typically 30-50)
- ✅ Candidates have scores (0.0-1.0)
- ✅ Cost is simulated ($0.02-$0.05)
- ✅ Execution time is reasonable (10-25 seconds)
- ✅ Results file is created
- ✅ Summary shows top candidates

## Troubleshooting

### Import Error

```bash
# Make sure you're in project root
pwd  # Should end with talent-acquisition-accelerator

# If not, navigate there
cd path/to/talent-acquisition-accelerator
```

### Module Not Found

```bash
# Install dependencies
pip install -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### No Results

Check the console output for error messages. Common issues:
- Invalid JSON in job file
- Missing required fields in job data
- Python version < 3.8

## Next Steps

1. ✅ Run basic workflow (you just did this!)
2. Review results file to understand output format
3. Try step-by-step mode to see each agent
4. Test all 3 scenarios
5. Proceed to Phase 4: Code Review

## Need Help?

- Check `local_dev/README.md` for detailed documentation
- Review `00_PHASE_3_COMPLETE.md` for implementation details
- Check agent code in `agents/` directory

## Success Criteria

You're ready for Phase 4 if:
- ✅ Workflow completes successfully
- ✅ All agents execute without errors
- ✅ Results look realistic and reasonable
- ✅ Cost simulation is within expected range
- ✅ You understand the workflow flow

**Congratulations! Your local environment is working. Ready for Phase 4!** 🎉
