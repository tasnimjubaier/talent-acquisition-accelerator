#!/bin/bash
# Verify Amazon Bedrock model access
# Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html

set -e

REGION=${AWS_REGION:-us-east-1}

echo "Verifying Amazon Bedrock access in region: $REGION"
echo ""

# List available foundation models
echo "Available Amazon Nova models:"
aws bedrock list-foundation-models \
  --region $REGION \
  --query 'modelSummaries[?contains(modelId, `nova`)].{ModelId:modelId,Name:modelName,Status:modelLifecycle.status}' \
  --output table

echo ""
echo "Checking model access status..."

# Check if we can access the models
if aws bedrock list-foundation-models --region $REGION --query 'modelSummaries[?contains(modelId, `nova`)]' --output text | grep -q "nova"; then
  echo "✅ Amazon Nova models are accessible!"
else
  echo "❌ Amazon Nova models not found. You may need to request access:"
  echo "   1. Go to Amazon Bedrock console"
  echo "   2. Navigate to 'Model access' in the left sidebar"
  echo "   3. Click 'Manage model access'"
  echo "   4. Select Amazon Nova models and submit request"
fi

echo ""
echo "Note: If models are not accessible, visit:"
echo "https://console.aws.amazon.com/bedrock/home?region=$REGION#/modelaccess"
