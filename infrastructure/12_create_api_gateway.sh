#!/bin/bash

################################################################################
# Script: 12_create_api_gateway.sh
# Purpose: Create API Gateway HTTP API for Talent Acquisition Accelerator
# Phase: 5.2 - API Gateway Setup
# Dependencies: Supervisor Lambda function must be deployed
################################################################################

set -e  # Exit on error

echo "=========================================="
echo "Creating API Gateway HTTP API"
echo "=========================================="

# Configuration
API_NAME="talent-acq-api"
LAMBDA_FUNCTION_NAME="talent-acq-supervisor"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo ""
echo "Configuration:"
echo "  API Name: $API_NAME"
echo "  Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "  Region: $REGION"
echo "  Account ID: $ACCOUNT_ID"
echo ""

# Step 1: Create HTTP API
echo "Step 1: Creating HTTP API..."
API_RESPONSE=$(aws apigatewayv2 create-api \
  --name "$API_NAME" \
  --protocol-type HTTP \
  --description "HTTP API for Talent Acquisition Accelerator multi-agent system" \
  --cors-configuration AllowOrigins="*",AllowMethods="POST,OPTIONS",AllowHeaders="Content-Type" \
  --region "$REGION" \
  --output json)

API_ID=$(echo "$API_RESPONSE" | jq -r '.ApiId')
API_ENDPOINT=$(echo "$API_RESPONSE" | jq -r '.ApiEndpoint')

if [ -z "$API_ID" ] || [ "$API_ID" == "null" ]; then
  echo "❌ Failed to create API"
  exit 1
fi

echo "✅ API created successfully"
echo "   API ID: $API_ID"
echo "   Endpoint: $API_ENDPOINT"

# Step 2: Create Lambda integration
echo ""
echo "Step 2: Creating Lambda integration..."

LAMBDA_ARN="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$LAMBDA_FUNCTION_NAME"

INTEGRATION_RESPONSE=$(aws apigatewayv2 create-integration \
  --api-id "$API_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "$LAMBDA_ARN" \
  --payload-format-version "2.0" \
  --region "$REGION" \
  --output json)

INTEGRATION_ID=$(echo "$INTEGRATION_RESPONSE" | jq -r '.IntegrationId')

if [ -z "$INTEGRATION_ID" ] || [ "$INTEGRATION_ID" == "null" ]; then
  echo "❌ Failed to create integration"
  exit 1
fi

echo "✅ Lambda integration created"
echo "   Integration ID: $INTEGRATION_ID"

# Step 3: Create route for POST /workflow
echo ""
echo "Step 3: Creating POST /workflow route..."

ROUTE_RESPONSE=$(aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key "POST /workflow" \
  --target "integrations/$INTEGRATION_ID" \
  --region "$REGION" \
  --output json)

ROUTE_ID=$(echo "$ROUTE_RESPONSE" | jq -r '.RouteId')

if [ -z "$ROUTE_ID" ] || [ "$ROUTE_ID" == "null" ]; then
  echo "❌ Failed to create route"
  exit 1
fi

echo "✅ Route created successfully"
echo "   Route ID: $ROUTE_ID"

# Step 4: Create default stage ($default)
echo ""
echo "Step 4: Creating default stage..."

STAGE_RESPONSE=$(aws apigatewayv2 create-stage \
  --api-id "$API_ID" \
  --stage-name '$default' \
  --auto-deploy \
  --region "$REGION" \
  --output json)

STAGE_NAME=$(echo "$STAGE_RESPONSE" | jq -r '.StageName')

echo "✅ Stage created successfully"
echo "   Stage: $STAGE_NAME"

# Step 5: Grant API Gateway permission to invoke Lambda
echo ""
echo "Step 5: Granting API Gateway invoke permissions..."

# Create unique statement ID
STATEMENT_ID="apigateway-invoke-$(date +%s)"

aws lambda add-permission \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --statement-id "$STATEMENT_ID" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/workflow" \
  --region "$REGION" \
  --output json > /dev/null

echo "✅ Lambda invoke permission granted"

# Step 6: Save API configuration
echo ""
echo "Step 6: Saving API configuration..."

cat > api_gateway_config.json << EOF
{
  "apiId": "$API_ID",
  "apiEndpoint": "$API_ENDPOINT",
  "integrationId": "$INTEGRATION_ID",
  "routeId": "$ROUTE_ID",
  "stageName": "$STAGE_NAME",
  "fullEndpoint": "$API_ENDPOINT/workflow",
  "region": "$REGION",
  "lambdaFunction": "$LAMBDA_FUNCTION_NAME"
}
EOF

echo "✅ Configuration saved to api_gateway_config.json"

# Summary
echo ""
echo "=========================================="
echo "API Gateway Setup Complete!"
echo "=========================================="
echo ""
echo "📋 API Details:"
echo "   API ID: $API_ID"
echo "   API Name: $API_NAME"
echo "   Region: $REGION"
echo ""
echo "🔗 Endpoint:"
echo "   $API_ENDPOINT/workflow"
echo ""
echo "📝 Usage:"
echo "   curl -X POST $API_ENDPOINT/workflow \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jobId\": \"test-job-001\"}'"
echo ""
echo "✅ Next Step: Run ./13_test_api_endpoint.sh to test the API"
echo ""
