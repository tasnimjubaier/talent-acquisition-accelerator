# Phase 5.2: API Gateway Setup - Quick Reference

**Status:** Ready for execution  
**Estimated Time:** 2-3 hours  
**Prerequisites:** Phase 5.1 complete (all agents deployed)

---

## Quick Start

### Step 1: Make Scripts Executable
```bash
cd infrastructure
chmod +x 12_create_api_gateway.sh
chmod +x 13_test_api_endpoint.sh
```

### Step 2: Create API Gateway
```bash
./12_create_api_gateway.sh
```

**Expected Output:**
- API Gateway HTTP API created
- Lambda integration configured
- POST /workflow route active
- Permissions granted
- Configuration saved to `api_gateway_config.json`

### Step 3: Test API Endpoint
```bash
./13_test_api_endpoint.sh
```

**Expected Output:**
- 5 tests executed
- All tests should pass
- Performance metrics displayed
- API endpoint URL confirmed

---

## Manual Testing

### Get API Endpoint
```bash
cat infrastructure/api_gateway_config.json | jq -r '.fullEndpoint'
```

### Test with cURL
```bash
# Replace {API_ENDPOINT} with your actual endpoint
curl -X POST {API_ENDPOINT} \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "manual-test-001",
    "jobTitle": "Software Engineer",
    "jobDescription": "Test job posting",
    "requiredSkills": ["Python", "AWS"],
    "location": "Remote",
    "experienceLevel": "Senior"
  }'
```

---

## Troubleshooting

### Issue: API Gateway creation fails
**Solution:**
```bash
# Check if API already exists
aws apigatewayv2 get-apis --query 'Items[?Name==`talent-acq-api`]'

# Delete existing API if needed
aws apigatewayv2 delete-api --api-id {API_ID}

# Re-run creation script
./12_create_api_gateway.sh
```

### Issue: Lambda permission denied
**Solution:**
```bash
# Check Lambda function exists
aws lambda get-function --function-name talent-acq-supervisor

# Check Lambda permissions
aws lambda get-policy --function-name talent-acq-supervisor

# Re-run permission grant
aws lambda add-permission \
  --function-name talent-acq-supervisor \
  --statement-id apigateway-invoke-$(date +%s) \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:*:*/*/POST/workflow"
```

### Issue: Test script fails
**Solution:**
```bash
# Check if jq is installed
which jq || brew install jq  # macOS
which jq || sudo apt-get install jq  # Linux

# Verify API Gateway config exists
ls -la infrastructure/api_gateway_config.json

# Check API Gateway status
aws apigatewayv2 get-api --api-id {API_ID}
```

---

## Verification Checklist

Before proceeding to Phase 6:

- [ ] `12_create_api_gateway.sh` executed successfully
- [ ] `api_gateway_config.json` file created
- [ ] API endpoint URL obtained
- [ ] `13_test_api_endpoint.sh` executed successfully
- [ ] All 5 tests passed
- [ ] Response time < 30 seconds
- [ ] CloudWatch logs show successful executions
- [ ] No AWS errors in console
- [ ] README.md updated with API documentation
- [ ] Phase 5.2 completion document reviewed

---

## Cost Check

```bash
# Check current AWS costs
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-16 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Should show minimal API Gateway costs (< $0.01)
```

---

## Next Phase

Once Phase 5.2 is verified complete:

**Phase 6: End-to-End Testing**
- Complete workflow validation
- Performance benchmarking
- Cost analysis
- Demo scenario preparation
- Documentation finalization

---

## Support Resources

- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)
- [Lambda Integration Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)
- [Troubleshooting API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-troubleshooting.html)

---

**Last Updated:** March 15, 2026
