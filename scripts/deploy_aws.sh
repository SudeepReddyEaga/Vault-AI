#!/usr/bin/env bash
# =========================================================================
# VAULT AI - AWS PRODUCTION CLUSTER DEPLOYMENT SCRIPT (Linux / macOS)
# =========================================================================

set -e

DOCKERHUB_USER=${1:-"pba"}
DOCKERHUB_PASS=${2:-""}
AWS_REGION=${3:-"us-east-1"}

echo "============================================================================"
echo "☁️ DEPLOYING VAULT AI TO AMAZON WEB SERVICES (AWS PROD CLUSTER)"
echo "============================================================================"

# 1. Check AWS Credentials
echo -e "\n[Step 1/4] Checking AWS Credentials..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "✅ AWS credentials active."
else
    echo "⚠️ Warning: AWS CLI not authenticated. Make sure AWS_ACCESS_KEY_ID is set."
fi

# 2. Run DevSecOps Gates
echo -e "\n[Step 2/4] Running DevSecOps Gates..."
python3 scripts/run_devsecops_pipeline.py

# 3. Terraform Apply
echo -e "\n[Step 3/4] Running Terraform on AWS..."
cd terraform
terraform init

TF_ARGS=("-var=enable_aws=true" "-var=aws_region=${AWS_REGION}")
if [ -n "$DOCKERHUB_PASS" ]; then
    TF_ARGS+=("-var=dockerhub_username=${DOCKERHUB_USER}" "-var=dockerhub_password=${DOCKERHUB_PASS}")
fi

terraform plan "${TF_ARGS[@]}"
terraform apply -auto-approve "${TF_ARGS[@]}"

echo -e "\n[Step 4/4] Infrastructure Provisioned Successfully!"
terraform output
cd ..
