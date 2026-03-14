#!/bin/bash
# Complete AWS infrastructure setup for Talent Acquisition Accelerator
# This script orchestrates all infrastructure setup steps

set -e

echo "=========================================="
echo "Talent Acquisition Accelerator"
echo "AWS Infrastructure Setup"
echo "=========================================="
echo ""

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "✓ AWS CLI configured"
echo "Account: $(aws sts get-caller-identity --query Account --output text)"
echo "Region: ${AWS_REGION:-us-east-1}"
echo ""

# Make scripts executable
chmod +x *.sh

# Step 1: Verify Bedrock Access
echo "Step 1: Verifying Amazon Bedrock access..."
./06_verify_bedrock_access.sh
echo ""

# Step 2: Create IAM Roles
echo "Step 2: Creating IAM roles..."
if aws iam get-role --role-name TalentAcqLambdaExecutionRole &> /dev/null; then
    echo "IAM role already exists, skipping..."
else
    ./03_create_iam_roles.sh
fi
echo ""

# Step 3: Create DynamoDB Tables
echo "Step 3: Creating DynamoDB tables..."
./04_create_dynamodb_tables.sh
echo ""

# Step 4: Create CloudWatch Log Groups
echo "Step 4: Creating CloudWatch Log Groups..."
./05_create_log_groups.sh
echo ""

echo "=========================================="
echo "✅ Infrastructure setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the created resources in AWS Console"
echo "2. Proceed to Phase 2: Core Services Setup"
echo "3. Implement shared utilities in ../shared/"
echo ""
echo "Resources created:"
echo "- IAM Role: TalentAcqLambdaExecutionRole"
echo "- DynamoDB Tables: 4 tables (talent-acq-*)"
echo "- CloudWatch Log Groups: 6 log groups"
echo ""
