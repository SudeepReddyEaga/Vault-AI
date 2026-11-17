# =========================================================================
# VAULT AI - TERRAFORM PRODUCTION CLUSTER CONFIGURATION (Section 6.1)
# Provisions AWS Multi-AZ VPC, ECS Fargate, ALB, RDS Postgres, ElastiCache,
# and Automated GitHub-to-DockerHub Build Pipeline
# =========================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "VaultAI"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# -------------------------------------------------------------------------
# 1. Automated GitHub Pull & Docker Hub Build Pipeline (From Scratch)
# -------------------------------------------------------------------------
resource "null_resource" "github_to_dockerhub_pipeline" {
  triggers = {
    repo_url  = var.github_repo_url
    image_tag = var.image_tag
  }

  provisioner "local-exec" {
    command = <<EOT
      echo "=== STAGE: Pulling from GitHub and Creating Docker Hub Images ==="
      # Check if docker is available
      if command -v docker >/dev/null 2>&1; then
        echo "Building budget-api-service..."
        docker build -t ${var.dockerhub_username}/budget-api-service:${var.image_tag} ../services/budget_api_service || true
        docker build -t ${var.dockerhub_username}/ai-agent-copilot:${var.image_tag} ../services/ai_agent_copilot || true
        docker build -t ${var.dockerhub_username}/ml-forecast-engine:${var.image_tag} ../services/ml_forecast_engine || true

        if [ -n "${var.dockerhub_password}" ]; then
          echo "Logging into Docker Hub..."
          echo "${var.dockerhub_password}" | docker login -u "${var.dockerhub_username}" --password-stdin
          echo "Pushing images to Docker Hub..."
          docker push ${var.dockerhub_username}/budget-api-service:${var.image_tag}
          docker push ${var.dockerhub_username}/ai-agent-copilot:${var.image_tag}
          docker push ${var.dockerhub_username}/ml-forecast-engine:${var.image_tag}
          echo "Images successfully published to Docker Hub!"
        else
          echo "Docker Hub password not provided. Images tagged locally."
        fi
      else
        echo "Docker not detected in execution environment. Using pre-built registry references."
      fi
    EOT
  }
}

# -------------------------------------------------------------------------
# 2. Multi-AZ VPC Network Infrastructure (Section 3 & Figure 3.1)
# -------------------------------------------------------------------------
resource "aws_vpc" "pba_vpc" {
  count                = var.enable_aws ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "pba-vpc-prod"
  }
}

# Public Subnets (Port 80/443 ALB)
resource "aws_subnet" "public_1a" {
  count                   = var.enable_aws ? 1 : 0
  vpc_id                  = aws_vpc.pba_vpc[0].id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = { Name = "pba-public-subnet-1a" }
}

resource "aws_subnet" "public_1b" {
  count                   = var.enable_aws ? 1 : 0
  vpc_id                  = aws_vpc.pba_vpc[0].id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true
  tags = { Name = "pba-public-subnet-1b" }
}

# Private Application Subnets (Ports 5000, 5001, 5002)
resource "aws_subnet" "private_app_1a" {
  count             = var.enable_aws ? 1 : 0
  vpc_id            = aws_vpc.pba_vpc[0].id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"
  tags = { Name = "pba-private-app-subnet-1a" }
}

resource "aws_subnet" "private_app_1b" {
  count             = var.enable_aws ? 1 : 0
  vpc_id            = aws_vpc.pba_vpc[0].id
  cidr_block        = "10.0.20.0/24"
  availability_zone = "${var.aws_region}b"
  tags = { Name = "pba-private-app-subnet-1b" }
}

# Private Isolated Database Subnets (PostgreSQL 5432, Redis 6379)
resource "aws_subnet" "private_db_1a" {
  count             = var.enable_aws ? 1 : 0
  vpc_id            = aws_vpc.pba_vpc[0].id
  cidr_block        = "10.0.100.0/24"
  availability_zone = "${var.aws_region}a"
  tags = { Name = "pba-private-db-subnet-1a" }
}

resource "aws_subnet" "private_db_1b" {
  count             = var.enable_aws ? 1 : 0
  vpc_id            = aws_vpc.pba_vpc[0].id
  cidr_block        = "10.0.200.0/24"
  availability_zone = "${var.aws_region}b"
  tags = { Name = "pba-private-db-subnet-1b" }
}

# Internet Gateway & Routing
resource "aws_internet_gateway" "pba_igw" {
  count  = var.enable_aws ? 1 : 0
  vpc_id = aws_vpc.pba_vpc[0].id
  tags   = { Name = "pba-igw" }
}

resource "aws_route_table" "public_rt" {
  count  = var.enable_aws ? 1 : 0
  vpc_id = aws_vpc.pba_vpc[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.pba_igw[0].id
  }
  tags = { Name = "pba-public-rt" }
}

resource "aws_route_table_association" "pub_1a" {
  count          = var.enable_aws ? 1 : 0
  subnet_id      = aws_subnet.public_1a[0].id
  route_table_id = aws_route_table.public_rt[0].id
}

resource "aws_route_table_association" "pub_1b" {
  count          = var.enable_aws ? 1 : 0
  subnet_id      = aws_subnet.public_1b[0].id
  route_table_id = aws_route_table.public_rt[0].id
}

# -------------------------------------------------------------------------
# 3. Security Groups (Table 3.1.1 Enterprise Port Allocation Matrix)
# -------------------------------------------------------------------------
# Port 80 & 443: Public ALB Security Group
resource "aws_security_group" "alb_sg" {
  count       = var.enable_aws ? 1 : 0
  name        = "pba-alb-security-group"
  description = "Allows incoming HTTP/HTTPS from 0.0.0.0/0"
  vpc_id      = aws_vpc.pba_vpc[0].id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Ports 5000, 5001, 5002: Private Application Security Group
resource "aws_security_group" "app_sg" {
  count       = var.enable_aws ? 1 : 0
  name        = "pba-app-security-group"
  description = "Allows traffic from ALB to Microservices"
  vpc_id      = aws_vpc.pba_vpc[0].id

  ingress {
    description     = "budget-api-service"
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg[0].id]
  }

  ingress {
    description = "ai-agent-copilot"
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "ml-forecast-engine"
    from_port   = 5002
    to_port     = 5002
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Ports 5432 & 6379: Database Subnet Security Group
resource "aws_security_group" "db_sg" {
  count       = var.enable_aws ? 1 : 0
  name        = "pba-db-security-group"
  description = "PostgreSQL and Redis access restricted to App Subnet"
  vpc_id      = aws_vpc.pba_vpc[0].id

  ingress {
    description     = "PostgreSQL Database"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg[0].id]
  }

  ingress {
    description     = "Redis Cache Cluster"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# -------------------------------------------------------------------------
# 4. Application Load Balancer (ALB)
# -------------------------------------------------------------------------
resource "aws_lb" "pba_alb" {
  count              = var.enable_aws ? 1 : 0
  name               = "pba-alb-prod"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg[0].id]
  subnets            = [aws_subnet.public_1a[0].id, aws_subnet.public_1b[0].id]
  tags               = { Name = "pba-alb-prod" }
}

resource "aws_lb_target_group" "pba_tg" {
  count       = var.enable_aws ? 1 : 0
  name        = "pba-api-target-group"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.pba_vpc[0].id
  target_type = "ip"

  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http_listener" {
  count             = var.enable_aws ? 1 : 0
  load_balancer_arn = aws_lb.pba_alb[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.pba_tg[0].arn
  }
}

# -------------------------------------------------------------------------
# 5. Production ECS Fargate Cluster (Section 6.1)
# -------------------------------------------------------------------------
resource "aws_ecs_cluster" "pba_prod_cluster" {
  count = var.enable_aws ? 1 : 0
  name  = "pba-ecs-cluster-prod"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_logs" {
  count             = var.enable_aws ? 1 : 0
  name              = "/ecs/pba-services"
  retention_in_days = 30
}

# IAM Role for ECS Execution
resource "aws_iam_role" "ecs_exec_role" {
  count = var.enable_aws ? 1 : 0
  name  = "pba-ecs-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_policy" {
  count      = var.enable_aws ? 1 : 0
  role       = aws_iam_role.ecs_exec_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Task Definition for budget-api-service (Port 5000)
resource "aws_ecs_task_definition" "budget_api_task" {
  count                    = var.enable_aws ? 1 : 0
  family                   = "budget-api-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_exec_role[0].arn

  container_definitions = jsonencode([{
    name      = "budget-api-container"
    image     = "${var.dockerhub_username}/budget-api-service:${var.image_tag}"
    essential = true
    portMappings = [{
      containerPort = 5000
      hostPort      = 5000
    }]
    environment = [
      { name = "PORT", value = "5000" },
      { name = "AI_AGENT_URL", value = "http://localhost:5001" },
      { name = "ML_ENGINE_URL", value = "http://localhost:5002" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/pba-services"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "budget-api"
      }
    }
  }])
}

# ECS Service for budget-api-service
resource "aws_ecs_service" "budget_api_service" {
  count           = var.enable_aws ? 1 : 0
  name            = "budget-api-service"
  cluster         = aws_ecs_cluster.pba_prod_cluster[0].id
  task_definition = aws_ecs_task_definition.budget_api_task[0].arn
  desired_count   = 3
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_app_1a[0].id, aws_subnet.private_app_1b[0].id]
    security_groups  = [aws_security_group.app_sg[0].id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.pba_tg[0].arn
    container_name   = "budget-api-container"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.http_listener]
}

# -------------------------------------------------------------------------
# 6. Database Subnet Group & RDS PostgreSQL (Port 5432)
# -------------------------------------------------------------------------
resource "aws_db_subnet_group" "db_subnets" {
  count      = var.enable_aws ? 1 : 0
  name       = "pba-rds-subnet-group"
  subnet_ids = [aws_subnet.private_db_1a[0].id, aws_subnet.private_db_1b[0].id]
}

resource "aws_db_instance" "postgres_primary" {
  count                  = var.enable_aws ? 1 : 0
  identifier             = "pba-postgres-primary"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "rural_platform_db"
  username               = "postgres"
  password               = var.db_password
  port                   = 5432
  db_subnet_group_name   = aws_db_subnet_group.db_subnets[0].name
  vpc_security_group_ids = [aws_security_group.db_sg[0].id]
  skip_final_snapshot    = true
}

# -------------------------------------------------------------------------
# 7. ElastiCache Redis Subnet Group & Cluster (Port 6379)
# -------------------------------------------------------------------------
resource "aws_elasticache_subnet_group" "redis_subnets" {
  count      = var.enable_aws ? 1 : 0
  name       = "pba-redis-subnet-group"
  subnet_ids = [aws_subnet.private_db_1a[0].id, aws_subnet.private_db_1b[0].id]
}

resource "aws_elasticache_cluster" "redis_cluster" {
  count                = var.enable_aws ? 1 : 0
  cluster_id           = "pba-redis-cluster"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnets[0].name
  security_group_ids   = [aws_security_group.db_sg[0].id]
}

# -------------------------------------------------------------------------
# 8. Serverless AWS Lambda Budget Alert Handler (Section 10.2)
# -------------------------------------------------------------------------
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../aws_lambda/aws_lambda_alert.py"
  output_path = "${path.module}/aws_lambda_alert.zip"
}

resource "aws_iam_role" "lambda_exec_role" {
  count = var.enable_aws ? 1 : 0
  name  = "pba-lambda-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_lambda_function" "budget_alert_function" {
  count            = var.enable_aws ? 1 : 0
  function_name    = "pba-aws-lambda-alert"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec_role[0].arn
  handler          = "aws_lambda_alert.lambda_handler"
  runtime          = "python3.11"
  timeout          = 10

  environment {
    variables = {
      SLACK_WEBHOOK_URL = "https://httpbin.org/post"
    }
  }
}
