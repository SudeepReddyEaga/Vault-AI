# =========================================================================
# VAULT AI - AWS PRODUCTION CLUSTER DEPLOYMENT SCRIPT (PowerShell)
# Clones latest from GitHub, builds Docker images, publishes to Docker Hub,
# and provisions AWS Multi-AZ VPC, ECS Fargate, ALB, RDS, and ElastiCache via Terraform
# =========================================================================

param(
    [string]$DockerHubUser = "pba",
    [string]$DockerHubPass = "",
    [string]$AwsRegion = "us-east-1"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "☁️ DEPLOYING VAULT AI TO AMAZON WEB SERVICES (AWS PROD CLUSTER)" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# 1. AWS Credentials Check
Write-Host "`n[Step 1/4] Checking AWS Credentials..." -ForegroundColor Yellow
$caller = aws sts get-caller-identity 2>$null
if ($caller) {
    Write-Host "✅ AWS Identity Verified: $caller" -ForegroundColor Green
} else {
    Write-Host "⚠️ Warning: AWS CLI not logged in or credentials not exported." -ForegroundColor Yellow
    Write-Host "Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set." -ForegroundColor Yellow
}

# 2. Run Pre-Flight DevSecOps Gates
Write-Host "`n[Step 2/4] Executing DevSecOps Quality & Security Gates..." -ForegroundColor Yellow
python scripts/run_devsecops_pipeline.py

# 3. Terraform Execution
Write-Host "`n[Step 3/4] Initializing and Applying Terraform Configuration..." -ForegroundColor Yellow
Set-Location terraform

terraform init

$tfVars = @()
if ($DockerHubPass -ne "") {
    $tfVars += "-var=dockerhub_username=$DockerHubUser"
    $tfVars += "-var=dockerhub_password=$DockerHubPass"
}
$tfVars += "-var=aws_region=$AwsRegion"
$tfVars += "-var=enable_aws=true"

Write-Host "Generating Terraform Execution Plan..." -ForegroundColor Yellow
terraform plan @tfVars

Write-Host "Applying Terraform Plan to AWS Cloud..." -ForegroundColor Yellow
terraform apply -auto-approve @tfVars

Write-Host "`n[Step 4/4] Extracting Deployed Cloud Infrastructure Endpoints..." -ForegroundColor Yellow
$albUrl = terraform output -raw alb_dns_name 2>$null
$cluster = terraform output -raw ecs_cluster_name 2>$null
$rds = terraform output -raw rds_postgres_endpoint 2>$null

Set-Location ..

Write-Host "`n============================================================================" -ForegroundColor Green
Write-Host "🎉 AWS DEPLOYMENT SUCCEEDED!" -ForegroundColor Green
Write-Host "• Application Load Balancer URL: http://$albUrl" -ForegroundColor White
Write-Host "• ECS Production Cluster:        $cluster" -ForegroundColor White
Write-Host "• RDS PostgreSQL Primary:        $rds:5432" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Green
