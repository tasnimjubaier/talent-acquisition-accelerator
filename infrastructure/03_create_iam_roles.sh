#!/bin/bash
# Create IAM roles and policies for Lambda execution
# Reference: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html

set -e

echo "Creating IAM role for Lambda execution..."

# Create IAM role
aws iam create-role \
  --role-name TalentAcqLambdaExecutionRole \
  --assume-role-policy-document file://01_lambda-trust-policy.json \
  --description "Execution role for Talent Acquisition Accelerator Lambda functions"

echo "✓ IAM role created"

# Attach custom policy
aws iam put-role-policy \
  --role-name TalentAcqLambdaExecutionRole \
  --policy-name TalentAcqLambdaPolicy \
  --policy-document file://02_lambda-execution-policy.json

echo "✓ Custom policy attached"

# Verify role creation
aws iam get-role --role-name TalentAcqLambdaExecutionRole

echo ""
echo "✅ IAM role setup complete!"
echo "Role ARN: $(aws iam get-role --role-name TalentAcqLambdaExecutionRole --query 'Role.Arn' --output text)"
