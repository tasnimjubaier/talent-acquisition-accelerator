#!/usr/bin/env python3
"""
Demo Execution Script

Runs demo scenarios and validates outputs for video recording.
Ensures all demo paths work reliably before recording.

Usage:
    python demo/04_run_demo.py --scenario SCENARIO-001
    python demo/04_run_demo.py --all
    python demo/04_run_demo.py --validate

Reference: 19_demo_data_preparation.md
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.supervisor_agent import SupervisorAgent
from shared.utils import format_duration, calculate_cost


class DemoRunner:
    """Executes and validates demo scenarios"""
    
    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.demo_dir = Path(__file__).parent
        self.results = []
    
    def load_demo_data(self) -> Dict[str, Any]:
        """Load demo jobs, candidates, and scenarios"""
        
        with open(self.demo_dir / "01_sample_jobs.json") as f:
            jobs = json.load(f)
        
        with open(self.demo_dir / "02_sample_candidates.json") as f:
            candidates = json.load(f)
        
        with open(self.demo_dir / "03_demo_scenarios.json") as f:
            scenarios = json.load(f)
        
        return {
            "jobs": jobs["jobs"],
            "candidates": candidates["candidates"],
            "scenarios": scenarios["scenarios"]
        }
    
    async def run_scenario(self, scenario: Dict[str, Any], jobs: List[Dict]) -> Dict[str, Any]:
        """Execute a single demo scenario"""
        
        print(f"\n{'='*60}")
        print(f"Running: {scenario['name']}")
        print(f"{'='*60}")
        
        # Find job for scenario
        job = next(j for j in jobs if j["job_id"] == scenario["job_id"])
        
        # Apply scenario config if present
        if "config" in scenario:
            job.update(scenario["config"])
        
        # Execute pipeline
        start_time = datetime.now()
        result = await self.supervisor.run_recruiting_pipeline(job)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Validate against expected outcomes
        validation = self.validate_scenario(result, scenario, execution_time)
        
        return {
            "scenario_id": scenario["scenario_id"],
            "scenario_name": scenario["name"],
            "status": result["status"],
            "execution_time": execution_time,
            "validation": validation,
            "result": result
        }
    
    def validate_scenario(self, result: Dict, scenario: Dict, execution_time: float) -> Dict:
        """Validate scenario results against expected outcomes"""
        
        validation = {
            "passed": True,
            "checks": [],
            "failures": []
        }
        
        if result["status"] != "completed":
            validation["passed"] = False
            validation["failures"].append("Pipeline did not complete successfully")
            return validation
        
        # Validate success criteria
        for criterion in scenario.get("success_criteria", []):
            check_result = self.check_criterion(criterion, result, execution_time)
            validation["checks"].append(check_result)
            
            if not check_result["passed"]:
                validation["passed"] = False
                validation["failures"].append(check_result["message"])
        
        return validation
    
    def check_criterion(self, criterion: str, result: Dict, execution_time: float) -> Dict:
        """Check a single success criterion"""
        
        if "execution time" in criterion.lower():
            target = float(criterion.split("<")[1].split("seconds")[0].strip())
            passed = execution_time < target
            return {
                "criterion": criterion,
                "passed": passed,
                "actual": f"{execution_time:.2f}s",
                "message": f"Execution time: {execution_time:.2f}s (target: < {target}s)"
            }
        
        if "cost" in criterion.lower():
            target = float(criterion.split("$")[1].strip())
            actual_cost = result.get("total_cost", 0)
            passed = actual_cost < target
            return {
                "criterion": criterion,
                "passed": passed,
                "actual": f"${actual_cost:.4f}",
                "message": f"Cost: ${actual_cost:.4f} (target: < ${target})"
            }
        
        # Default pass for other criteria
        return {
            "criterion": criterion,
            "passed": True,
            "message": "Manual validation required"
        }
    
    def print_results(self, scenario_result: Dict):
        """Print scenario results"""
        
        print(f"\n{'='*60}")
        print(f"Results: {scenario_result['scenario_name']}")
        print(f"{'='*60}")
        print(f"Status: {scenario_result['status']}")
        print(f"Execution Time: {scenario_result['execution_time']:.2f}s")
        print(f"Validation: {'✅ PASSED' if scenario_result['validation']['passed'] else '❌ FAILED'}")
        
        if scenario_result['validation']['failures']:
            print(f"\nFailures:")
            for failure in scenario_result['validation']['failures']:
                print(f"  ❌ {failure}")
        
        print(f"\nChecks:")
        for check in scenario_result['validation']['checks']:
            status = "✅" if check['passed'] else "❌"
            print(f"  {status} {check['message']}")


async def main():
    parser = argparse.ArgumentParser(description="Run demo scenarios")
    parser.add_argument("--scenario", help="Specific scenario ID to run")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--validate", action="store_true", help="Run validation checks")
    
    args = parser.parse_args()
    
    runner = DemoRunner()
    demo_data = runner.load_demo_data()
    
    if args.all:
        print("Running all demo scenarios...")
        for scenario in demo_data["scenarios"]:
            result = await runner.run_scenario(scenario, demo_data["jobs"])
            runner.print_results(result)
    
    elif args.scenario:
        scenario = next(s for s in demo_data["scenarios"] if s["scenario_id"] == args.scenario)
        result = await runner.run_scenario(scenario, demo_data["jobs"])
        runner.print_results(result)
    
    else:
        print("Please specify --scenario SCENARIO-ID or --all")


if __name__ == "__main__":
    asyncio.run(main())
