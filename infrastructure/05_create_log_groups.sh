#!/bin/bash
# Create CloudWatch Log Groups for Lambda functions
# Reference: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html

set -e

REGION=${AWS_REGION:-us-east-1}
RETENTION_DAYS=30

echo "Creating CloudWatch Log Groups in region: $REGION"
echo ""

# Array of agent names
agents=("supervisor" "sourcing" "screening" "outreach" "scheduling" "evaluation")

# Create log groups
for agent in "${agents[@]}"; do
  echo "Creating log group for $agent agent..."
  aws logs create-log-group \
    --log-group-name /aws/lambda/talent-acq-$agent \
    --region $REGION 2>/dev/null || echo "  (already exists)"
  
  # Set retention policy
  aws logs put-retention-policy \
    --log-group-name /aws/lambda/talent-acq-$agent \
    --retention-in-days $RETENTION_DAYS \
    --region $REGION
  
  echo "✓ Log group created with $RETENTION_DAYS day retention"
done

echo ""
echo "✅ All CloudWatch Log Groups created successfully!"
echo ""
echo "Log Groups:"
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/talent-acq \
  --region $REGION \
  --query 'logGroups[*].[logGroupName,retentionInDays]' \
  --output table
