#!/bin/bash
# Test infrastructure scripts for syntax and structure
# This validates the scripts without executing them on AWS

set -e

echo "=========================================="
echo "Infrastructure Scripts Validation"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Test 1: Check all required files exist
echo "Test 1: Checking required files..."
required_files=(
  "00_setup_aws.sh"
  "01_lambda-trust-policy.json"
  "02_lambda-execution-policy.json"
  "03_create_iam_roles.sh"
  "04_create_dynamodb_tables.sh"
  "05_create_log_groups.sh"
  "06_verify_bedrock_access.sh"
)

for file in "${required_files[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✓ $file exists"
  else
    echo "  ✗ $file missing"
    exit 1
  fi
done
echo ""

# Test 2: Validate JSON syntax
echo "Test 2: Validating JSON files..."
for json_file in *.json; do
  if python3 -m json.tool "$json_file" > /dev/null 2>&1; then
    echo "  ✓ $json_file - valid JSON"
  else
    echo "  ✗ $json_file - invalid JSON"
    exit 1
  fi
done
echo ""

# Test 3: Check shell script syntax
echo "Test 3: Checking shell script syntax..."
for script in *.sh; do
  if [ "$script" != "07_test_scripts.sh" ]; then
    if bash -n "$script" 2>/dev/null; then
      echo "  ✓ $script - syntax OK"
    else
      echo "  ✗ $script - syntax error"
      bash -n "$script"
      exit 1
    fi
  fi
done
echo ""

# Test 4: Check scripts are executable
echo "Test 4: Checking file permissions..."
for script in *.sh; do
  if [ -x "$script" ]; then
    echo "  ✓ $script - executable"
  else
    echo "  ⚠ $script - not executable (run: chmod +x $script)"
  fi
done
echo ""

# Test 5: Verify JSON structure
echo "Test 5: Verifying IAM policy structure..."

# Check trust policy has required fields
if grep -q "AssumeRole" 01_lambda-trust-policy.json && \
   grep -q "lambda.amazonaws.com" 01_lambda-trust-policy.json; then
  echo "  ✓ Trust policy structure valid"
else
  echo "  ✗ Trust policy missing required fields"
  exit 1
fi

# Check execution policy has required permissions
if grep -q "bedrock:InvokeModel" 02_lambda-execution-policy.json && \
   grep -q "dynamodb:GetItem" 02_lambda-execution-policy.json && \
   grep -q "logs:CreateLogGroup" 02_lambda-execution-policy.json; then
  echo "  ✓ Execution policy has required permissions"
else
  echo "  ✗ Execution policy missing required permissions"
  exit 1
fi
echo ""

# Test 6: Check for hardcoded values that should be variables
echo "Test 6: Checking for proper variable usage..."
issues=0
for script in *.sh; do
  if [ "$script" != "07_test_scripts.sh" ]; then
    # Check if region is parameterized
    if grep -q "us-east-1" "$script" && ! grep -q "AWS_REGION" "$script"; then
      echo "  ⚠ $script - region might be hardcoded"
      issues=$((issues + 1))
    fi
  fi
done

if [ $issues -eq 0 ]; then
  echo "  ✓ All scripts use proper variables"
else
  echo "  ⚠ Found $issues potential issues (not critical)"
fi
echo ""

echo "=========================================="
echo "✅ All validation tests passed!"
echo "=========================================="
echo ""
echo "Scripts are ready to use. To execute:"
echo "  1. Configure AWS CLI: aws configure"
echo "  2. Run: ./00_setup_aws.sh"
echo ""
