#!/bin/bash
# Create DynamoDB tables for the Talent Acquisition Accelerator
# Reference: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/getting-started-step-1.html

set -e

REGION=${AWS_REGION:-us-east-1}

echo "Creating DynamoDB tables in region: $REGION"
echo ""

# Create Candidates Table
echo "Creating talent-acq-candidates table..."
aws dynamodb create-table \
  --table-name talent-acq-candidates \
  --attribute-definitions \
    AttributeName=candidateId,AttributeType=S \
    AttributeName=jobId,AttributeType=S \
  --key-schema \
    AttributeName=candidateId,KeyType=HASH \
  --global-secondary-indexes \
    '[{
      "IndexName": "JobIdIndex",
      "KeySchema": [{"AttributeName":"jobId","KeyType":"HASH"}],
      "Projection": {"ProjectionType":"ALL"},
      "ProvisionedThroughput": {"ReadCapacityUnits":5,"WriteCapacityUnits":5}
    }]' \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "✓ Candidates table created"
echo ""

# Create Jobs Table
echo "Creating talent-acq-jobs table..."
aws dynamodb create-table \
  --table-name talent-acq-jobs \
  --attribute-definitions \
    AttributeName=jobId,AttributeType=S \
  --key-schema \
    AttributeName=jobId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "✓ Jobs table created"
echo ""

# Create Interactions Table
echo "Creating talent-acq-interactions table..."
aws dynamodb create-table \
  --table-name talent-acq-interactions \
  --attribute-definitions \
    AttributeName=interactionId,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
    AttributeName=candidateId,AttributeType=S \
  --key-schema \
    AttributeName=interactionId,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --global-secondary-indexes \
    '[{
      "IndexName": "CandidateIdIndex",
      "KeySchema": [{"AttributeName":"candidateId","KeyType":"HASH"}],
      "Projection": {"ProjectionType":"ALL"},
      "ProvisionedThroughput": {"ReadCapacityUnits":5,"WriteCapacityUnits":5}
    }]' \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "✓ Interactions table created"
echo ""

# Create Agent State Table
echo "Creating talent-acq-agent-state table..."
aws dynamodb create-table \
  --table-name talent-acq-agent-state \
  --attribute-definitions \
    AttributeName=stateId,AttributeType=S \
  --key-schema \
    AttributeName=stateId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "✓ Agent state table created"
echo ""

# Wait for tables to become active
echo "Waiting for tables to become active..."
aws dynamodb wait table-exists --table-name talent-acq-candidates --region $REGION
aws dynamodb wait table-exists --table-name talent-acq-jobs --region $REGION
aws dynamodb wait table-exists --table-name talent-acq-interactions --region $REGION
aws dynamodb wait table-exists --table-name talent-acq-agent-state --region $REGION

echo ""
echo "✅ All DynamoDB tables created successfully!"
echo ""
echo "Tables:"
aws dynamodb list-tables --region $REGION --query 'TableNames[?starts_with(@, `talent-acq`)]' --output table
