#!/bin/bash

# Update IAM Permissions for Lambda-to-Lambda Invocation
# This script adds Lambda invoke permissions to the existing execution role
# Reference: 16_module_build_checklist.md - Phase 5, Step 5.2

set -e

echo "=========================================="
echo "Updating IAM Permissions for Lambda Invocation"
echo "=========================================="

ROLE_NAME="TalentAcqLambdaExecutionRole"
POLICY_NAME="LambdaInvokePolicy"
POLICY_FILE="09_lambda_invoke_policy.json"

# Check if role exists
echo "Checking if IAM role exists..."
if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
    echo "❌ Error: IAM role $ROLE_NAME not found"
    echo "Please run 03_create_iam_roles.sh first"
    exit 1
fi

echo "✅ IAM role found: $ROLE_NAME"

# Check if policy file exists
if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ Error: Policy file $POLICY_FILE not found"
    exit 1
fi

echo "✅ Policy file found: $POLICY_FILE"

# Attach inline policy to role
echo "Attaching Lambda invoke policy to role..."
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name $POLICY_NAME \
  --policy-document file://$POLICY_FILE

echo "✅ Policy attached successfully"

# Verify policy was attached
echo "Verifying policy attachment..."
if aws iam get-role-policy --role-name $ROLE_NAME --policy-name $POLICY_NAME &> /dev/null; then
    echo "✅ Policy verification successful"
else
    echo "❌ Policy verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ IAM Permissions Updated Successfully"
echo "=========================================="
echo ""
echo "The Lambda execution role now has permission to invoke other Lambda functions."
echo "Role: $ROLE_NAME"
echo "Policy: $POLICY_NAME"
echo ""
echo "Next steps:"
echo "1. Deploy Lambda functions: ./11_deploy_all_agents.sh"
echo "2. Test agent invocation"
echo ""
