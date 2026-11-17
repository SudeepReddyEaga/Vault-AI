output "alb_dns_name" {
  description = "Application Load Balancer Public DNS URL (Port 80/443)"
  value       = var.enable_aws ? aws_lb.pba_alb[0].dns_name : "http://localhost:80"
}

output "ecs_cluster_name" {
  description = "ECS Fargate Production Cluster Name"
  value       = var.enable_aws ? aws_ecs_cluster.pba_prod_cluster[0].name : "pba-ecs-cluster-prod"
}

output "rds_postgres_endpoint" {
  description = "RDS PostgreSQL Connection Hostname (Port 5432)"
  value       = var.enable_aws ? aws_db_instance.postgres_primary[0].address : "localhost:5432"
}

output "redis_cluster_endpoint" {
  description = "ElastiCache Redis Primary Node Endpoint (Port 6379)"
  value       = var.enable_aws ? aws_elasticache_cluster.redis_cluster[0].cache_nodes[0].address : "localhost:6379"
}

output "budget_api_service_url" {
  description = "budget-api-service URL"
  value       = var.enable_aws ? "http://${aws_lb.pba_alb[0].dns_name}:5000" : "http://localhost:5000"
}

output "grafana_dashboard_url" {
  description = "Grafana Observability Dashboard URL"
  value       = "http://localhost:3000"
}

output "prometheus_server_url" {
  description = "Prometheus Metrics Server URL"
  value       = "http://localhost:9090"
}
