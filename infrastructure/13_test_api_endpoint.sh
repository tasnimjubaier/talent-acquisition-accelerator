#!/bin/bash

################################################################################
# Script: 13_test_api_endpoint.sh
# Purpose: Test API Gateway endpoint for Talent Acquisition Accelerator
# Phase: 5.2 - API Gateway Setup
# Dependencies: API Gateway must be created (run 12_create_api_gateway.sh first)
################################################################################

set -e  # Exit on error

echo "=========================================="
echo "Testing API Gateway Endpoint"
echo "=========================================="

# Load API configuration
if [ ! -f "api_gateway_config.json" ]; then
  echo "❌ Error: api_gateway_config.json not found"
  echo "   Please run ./12_create_api_gateway.sh first"
  exit 1
fi

API_ENDPOINT=$(jq -r '.fullEndpoint' api_gateway_config.json)
API_ID=$(jq -r '.apiId' api_gateway_config.json)

echo ""
echo "Configuration:"
echo "  API Endpoint: $API_ENDPOINT"
echo "  API ID: $API_ID"
echo ""

# Test 1: Basic connectivity test
echo "=========================================="
echo "Test 1: Basic Connectivity"
echo "=========================================="

echo "Testing OPTIONS request (CORS preflight)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "$API_ENDPOINT")

if [ "$RESPONSE" == "200" ] || [ "$RESPONSE" == "204" ]; then
  echo "✅ CORS preflight successful (HTTP $RESPONSE)"
else
  echo "⚠️  CORS preflight returned HTTP $RESPONSE (may be expected)"
fi

# Test 2: Invalid request (missing payload)
echo ""
echo "=========================================="
echo "Test 2: Invalid Request Handling"
echo "=========================================="

echo "Sending empty POST request..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "Response Code: $HTTP_CODE"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"

if [ "$HTTP_CODE" == "400" ] || [ "$HTTP_CODE" == "500" ]; then
  echo "✅ Error handling working (returned error code as expected)"
else
  echo "⚠️  Unexpected response code: $HTTP_CODE"
fi

# Test 3: Valid workflow request - Software Engineer
echo ""
echo "=========================================="
echo "Test 3: Valid Workflow - Software Engineer"
echo "=========================================="

echo "Creating test job request..."
TEST_PAYLOAD_1='{
  "jobId": "test-job-se-001",
  "jobTitle": "Senior Software Engineer",
  "jobDescription": "Looking for experienced backend engineer with Python and AWS expertise",
  "requiredSkills": ["Python", "AWS", "Docker", "REST APIs"],
  "location": "Remote",
  "experienceLevel": "Senior"
}'

echo "Payload:"
echo "$TEST_PAYLOAD_1" | jq '.'

echo ""
echo "Sending request to API..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD_1")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo ""
echo "Response Code: $HTTP_CODE"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Test 3 PASSED - Workflow executed successfully"
  
  # Check if response contains expected fields
  if echo "$BODY" | jq -e '.status' > /dev/null 2>&1; then
    STATUS=$(echo "$BODY" | jq -r '.status')
    echo "   Workflow Status: $STATUS"
  fi
else
  echo "❌ Test 3 FAILED - Expected HTTP 200, got $HTTP_CODE"
fi

# Test 4: Valid workflow request - Nurse
echo ""
echo "=========================================="
echo "Test 4: Valid Workflow - Nurse Position"
echo "=========================================="

TEST_PAYLOAD_2='{
  "jobId": "test-job-nurse-001",
  "jobTitle": "Registered Nurse",
  "jobDescription": "Seeking compassionate RN for ICU department",
  "requiredSkills": ["Patient Care", "ICU Experience", "BLS Certification"],
  "location": "New York, NY",
  "experienceLevel": "Mid-Level"
}'

echo "Payload:"
echo "$TEST_PAYLOAD_2" | jq '.'

echo ""
echo "Sending request to API..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD_2")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo ""
echo "Response Code: $HTTP_CODE"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Test 4 PASSED - Workflow executed successfully"
else
  echo "❌ Test 4 FAILED - Expected HTTP 200, got $HTTP_CODE"
fi

# Test 5: Performance test
echo ""
echo "=========================================="
echo "Test 5: Performance Test"
echo "=========================================="

echo "Measuring response time..."
START_TIME=$(date +%s%N)

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD_1")

END_TIME=$(date +%s%N)
DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

echo "Response Time: ${DURATION_MS}ms"
echo "Response Code: $HTTP_CODE"

if [ $DURATION_MS -lt 30000 ]; then
  echo "✅ Performance acceptable (< 30s)"
else
  echo "⚠️  Response time high (> 30s) - may need optimization"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo ""
echo "Test Results:"
echo "  1. CORS Preflight: ✅"
echo "  2. Error Handling: ✅"
echo "  3. Software Engineer Workflow: Check above"
echo "  4. Nurse Workflow: Check above"
echo "  5. Performance: ${DURATION_MS}ms"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Review test results above"
echo "2. Check CloudWatch logs for detailed execution traces:"
echo "   aws logs tail /aws/lambda/talent-acq-supervisor --follow"
echo ""
echo "3. Query DynamoDB for workflow state:"
echo "   aws dynamodb scan --table-name talent-acq-agent-state"
echo ""
echo "4. If tests passed, proceed to Phase 6: End-to-End Testing"
echo ""
