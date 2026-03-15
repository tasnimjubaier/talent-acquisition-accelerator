#!/bin/bash

# Deploy All Lambda Functions
# This script packages and deploys all 6 Lambda functions (Supervisor + 5 Workers)
# Reference: 16_module_build_checklist.md - Phase 5, Step 5.3

set -e

echo "=========================================="
echo "Deploying All Lambda Functions"
echo "=========================================="

# Configuration
ROLE_NAME="TalentAcqLambdaExecutionRole"
REGION="${AWS_REGION:-us-east-1}"
RUNTIME="python3.12"
TIMEOUT=300
MEMORY=512

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "Configuration:"
echo "  Region: $REGION"
echo "  Runtime: $RUNTIME"
echo "  Role ARN: $ROLE_ARN"
echo ""

# Create deployment directory
DEPLOY_DIR="deployment"
mkdir -p $DEPLOY_DIR

# Agent list
AGENTS=("supervisor" "sourcing" "screening" "outreach" "scheduling" "evaluation")

# Function to deploy an agent
deploy_agent() {
    local agent_name=$1
    local function_name="talent-acq-${agent_name}"
    
    echo "----------------------------------------"
    echo "Deploying: $function_name"
    echo "----------------------------------------"
    
    # Create agent-specific deployment directory
    local agent_deploy_dir="${DEPLOY_DIR}/${agent_name}"
    rm -rf $agent_deploy_dir
    mkdir -p $agent_deploy_dir
    
    # Copy agent code
    cp "../agents/${agent_name}_agent.py" "${agent_deploy_dir}/lambda_function.py"
    
    # Copy shared modules
    cp -r ../shared "${agent_deploy_dir}/"
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -q -r ../requirements.txt -t "${agent_deploy_dir}/" --upgrade
    
    # Create deployment package
    echo "Creating deployment package..."
    cd $agent_deploy_dir
    zip -q -r "../${agent_name}_agent.zip" .
    cd - > /dev/null
    
    # Check if function exists
    if aws lambda get-function --function-name $function_name --region $REGION &> /dev/null; then
        echo "Updating existing function..."
        aws lambda update-function-code \
          --function-name $function_name \
          --zip-file "fileb://${DEPLOY_DIR}/${agent_name}_agent.zip" \
          --region $REGION \
          --output text > /dev/null
        
        echo "✅ Function updated: $function_name"
    else
        echo "Creating new function..."
        aws lambda create-function \
          --function-name $function_name \
          --runtime $RUNTIME \
          --role $ROLE_ARN \
          --handler lambda_function.lambda_handler \
          --zip-file "fileb://${DEPLOY_DIR}/${agent_name}_agent.zip" \
          --timeout $TIMEOUT \
          --memory-size $MEMORY \
          --region $REGION \
          --output text > /dev/null
        
        echo "✅ Function created: $function_name"
    fi
    
    echo ""
}

# Deploy all agents
for agent in "${AGENTS[@]}"; do
    deploy_agent $agent
done

echo "=========================================="
echo "✅ All Lambda Functions Deployed"
echo "=========================================="
echo ""
echo "Deployed functions:"
for agent in "${AGENTS[@]}"; do
    echo "  - talent-acq-${agent}"
done
echo ""
echo "Next steps:"
echo "1. Test individual agents"
echo "2. Test end-to-end workflow"
echo "3. Set up API Gateway: ./12_create_api_gateway.sh"
echo ""
