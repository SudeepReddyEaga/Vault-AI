variable "enable_aws" {
  description = "Set to true to provision AWS cloud resources; set to false for local/offline dry-run."
  type        = bool
  default     = true
}

variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "IPv4 CIDR block for PBA VPC (Section 3 DEVOPSPRESUB)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "github_repo_url" {
  description = "GitHub repository URL to clone and build from scratch"
  type        = string
  default     = "https://github.com/sudee/VaultAI.git"
}

variable "dockerhub_username" {
  description = "Docker Hub username/organization for image registry release"
  type        = string
  default     = "pba"
}

variable "dockerhub_password" {
  description = "Docker Hub token or password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "image_tag" {
  description = "Docker image tag release version"
  type        = string
  default     = "latest"
}

variable "db_password" {
  description = "PostgreSQL RDS Master Password"
  type        = string
  default     = "postgrespassword2026"
  sensitive   = true
}
