# Testing Infrastructure Scripts

**Document:** 01_testing_infrastructure.md  
**Purpose:** Manual testing guide for infrastructure scripts before AWS deployment  
**Phase:** Phase 1 - Infrastructure Foundation

---

## Overview

This guide provides step-by-step instructions to validate all infrastructure scripts and configuration files before executing them on AWS. Testing locally ensures syntax correctness and proper structure without incurring AWS costs.

---

## Prerequisites

Before testing, ensure you have:

- Bash shell (macOS/Linux) or Git Bash (Windows)
- Python 3.x installed (for JSON validation)
- Terminal access to the project directory

---

## Testing Steps

### Step 1: Navigate to Infrastructure Directory

```bash
cd 00_ops/01_job/07_products/00_amazon_nova_hackathon/talent-acquisition-accelerator/infrastructure
```

### Step 2: Make Scripts Executable

```bash
chmod +x *.sh
```

**Expected:** No output, command completes silently.

### Step 3: Validate JSON Files

Test the IAM policy JSON files for syntax errors:

```bash
# Test Lambda trust policy
python3 -m json.tool 01_lambda-trust-policy.json

# Test Lambda execution policy
python3 -m json.tool 02_lambda-execution-policy.json
```

**Expected Output:** Formatted JSON displayed without errors.

**Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    ...
  ]
}
```

**If errors occur:** Check for missing commas, brackets, or quotes in JSON files.


### Step 4: Check Shell Script Syntax

Validate each shell script without executing it:

```bash
# Test main setup script
bash -n 00_setup_aws.sh

# Test IAM role creation
bash -n 03_create_iam_roles.sh

# Test DynamoDB table creation
bash -n 04_create_dynamodb_tables.sh

# Test CloudWatch log groups
bash -n 05_create_log_groups.sh

# Test Bedrock verification
bash -n 06_verify_bedrock_access.sh

# Test validation script
bash -n 07_test_scripts.sh
```

**Expected:** No output means syntax is valid.

**If errors occur:** The error message will indicate the line number and issue.

### Step 5: Verify File Structure

```bash
# List all files with details
ls -lah
```

**Expected Files:**
- `00_setup_aws.sh` - Main orchestration script
- `01_lambda-trust-policy.json` - Lambda trust relationship
- `02_lambda-execution-policy.json` - Lambda permissions
- `03_create_iam_roles.sh` - IAM role setup
- `04_create_dynamodb_tables.sh` - Database creation
- `05_create_log_groups.sh` - Logging setup
- `06_verify_bedrock_access.sh` - Bedrock verification
- `07_test_scripts.sh` - Automated validation
- `README.md` - Infrastructure documentation

### Step 6: Verify Project Structure

```bash
# Go back to project root
cd ..

# Check directory structure
ls -la
```

**Expected Directories:**
- `agents/` - Agent implementations
- `demo/` - Demo data and scripts
- `docs/` - Documentation
- `infrastructure/` - AWS setup scripts
- `shared/` - Shared utilities
- `tests/` - Unit and integration tests

**Expected Files:**
- `.gitignore`
- `LICENSE`
- `README.md`
- `requirements.txt`


---

## Validation Checklist

Use this checklist to confirm all tests pass:

- [ ] All shell scripts are executable (chmod completed)
- [ ] `01_lambda-trust-policy.json` parses correctly
- [ ] `02_lambda-execution-policy.json` parses correctly
- [ ] `00_setup_aws.sh` has no syntax errors
- [ ] `03_create_iam_roles.sh` has no syntax errors
- [ ] `04_create_dynamodb_tables.sh` has no syntax errors
- [ ] `05_create_log_groups.sh` has no syntax errors
- [ ] `06_verify_bedrock_access.sh` has no syntax errors
- [ ] `07_test_scripts.sh` has no syntax errors
- [ ] All expected files are present
- [ ] All expected directories exist with README files

---

## Troubleshooting

### JSON Parsing Errors

**Error:** `Expecting property name enclosed in double quotes`

**Solution:** Check for:
- Missing commas between array/object elements
- Trailing commas (not allowed in JSON)
- Single quotes instead of double quotes
- Missing closing brackets or braces

### Shell Script Syntax Errors

**Error:** `unexpected token near...`

**Solution:** Check for:
- Missing `fi` to close `if` statements
- Missing `done` to close loops
- Unclosed quotes or brackets
- Incorrect variable syntax

### Permission Denied

**Error:** `Permission denied` when running scripts

**Solution:** Run `chmod +x *.sh` in the infrastructure directory

---

## Next Steps

Once all tests pass:

1. Review the AWS setup requirements in `infrastructure/README.md`
2. Ensure AWS CLI is installed and configured
3. Verify AWS account has necessary permissions
4. Proceed to Phase 2: Core Services Setup

---

## Verification Sources

- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [Bash Script Testing](https://www.shellcheck.net/) - Online shell script validator
- [JSON Validator](https://jsonlint.com/) - Online JSON syntax checker
