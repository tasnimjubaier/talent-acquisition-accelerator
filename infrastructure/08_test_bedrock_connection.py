#!/usr/bin/env python3
"""
Test Bedrock Connection

Standalone script to verify Amazon Bedrock access and Nova model invocation.
Run this after IAM roles are created to validate Phase 2 setup.

Usage:
    python infrastructure/08_test_bedrock_connection.py

References:
- 16_module_build_checklist.md: Phase 2 verification
- 02_tech_stack_decisions.md: Nova 2 Lite configuration

Verification Sources:
- Amazon Bedrock Converse API: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils import invoke_bedrock
from shared.config import Config


def test_bedrock_connection():
    """Test Bedrock connection and Nova model invocation"""
    
    print("=" * 70)
    print("Testing Amazon Bedrock Connection")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Region: {Config.AWS_REGION}")
    print(f"  Model: {Config.BEDROCK_MODEL_ID}")
    print(f"  Max Tokens: {Config.MAX_TOKENS}")
    print(f"  Temperature: {Config.TEMPERATURE}")
    print("\n" + "-" * 70)
    
    # Test 1: Simple invocation
    print("\nTest 1: Simple text generation")
    print("-" * 70)
    
    result = invoke_bedrock(
        prompt="Say 'Bedrock connection successful' if you can read this.",
        max_tokens=50
    )

    
    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Response: {result['content']}")
        print(f"   Input tokens: {result['input_tokens']}")
        print(f"   Output tokens: {result['output_tokens']}")
        print(f"   Cost: ${result['cost_usd']:.6f}")
        print(f"   Latency: {result['latency']:.2f}s")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.get('error')}")
        print(f"   Error code: {result.get('error_code')}")
        return False
    
    # Test 2: Structured output (JSON)
    print("\n" + "-" * 70)
    print("\nTest 2: Structured JSON output")
    print("-" * 70)
    
    result = invoke_bedrock(
        prompt="""Generate a JSON object with candidate information:
        {
            "name": "John Doe",
            "skills": ["Python", "AWS", "Machine Learning"],
            "experience_years": 5
        }
        Return only the JSON, no other text.""",
        max_tokens=100
    )
    
    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Response: {result['content'][:200]}...")
        print(f"   Cost: ${result['cost_usd']:.6f}")
        
        # Try to parse as JSON
        try:
            json.loads(result['content'])
            print(f"   ✅ Valid JSON")
        except json.JSONDecodeError:
            print(f"   ⚠️  Not valid JSON (may need prompt tuning)")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.get('error')}")
        return False
    
    # Test 3: System prompt
    print("\n" + "-" * 70)
    print("\nTest 3: System prompt usage")
    print("-" * 70)
    
    result = invoke_bedrock(
        prompt="What is your role?",
        system_prompt="You are a recruiting assistant helping to screen candidates.",
        max_tokens=50
    )
    
    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Response: {result['content']}")
        print(f"   Cost: ${result['cost_usd']:.6f}")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.get('error')}")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ All tests passed! Bedrock connection is working correctly.")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run unit tests: pytest tests/test_utils.py -v")
    print("  2. Proceed to Phase 3: Agent implementation")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = test_bedrock_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
