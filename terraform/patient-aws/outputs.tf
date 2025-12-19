# ========================================
# Network Outputs
# ========================================
output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.network.private_subnet_ids
}

# ========================================
# Database Outputs
# ========================================
output "db_endpoint" {
  description = "RDS endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "db_name" {
  description = "Database name"
  value       = module.database.db_name
}

# ========================================
# Application Outputs
# ========================================
output "alb_dns_name" {
  description = "ALB DNS name - use this to access the backend API"
  value       = module.app_cluster.alb_dns_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend Docker images"
  value       = module.app_cluster.ecr_repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.app_cluster.ecs_cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.app_cluster.ecs_service_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for ECS tasks"
  value       = module.app_cluster.cloudwatch_log_group_name
}

# ========================================
# Frontend Outputs
# ========================================
output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.static_site.s3_bucket_name
}

output "cloudfront_url" {
  description = "CloudFront distribution URL - use this to access the frontend"
  value       = "https://${module.static_site.cloudfront_domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = module.static_site.cloudfront_distribution_id
}

# ========================================
# Deployment Instructions
# ========================================
output "deployment_instructions" {
  description = "Next steps for deployment"
  value = <<-EOT

    ========================================
    Cloud Doctor MVP - Patient Zone
    ========================================

    ✅ Infrastructure successfully provisioned!

    📋 Next Steps:

    1. Build and push backend Docker image:
       cd ../../patient-aws/backend
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.app_cluster.ecr_repository_url}
       docker build -t ${module.app_cluster.ecr_repository_url}:latest .
       docker push ${module.app_cluster.ecr_repository_url}:latest

    2. Update ECS service to pull new image:
       aws ecs update-service --cluster ${module.app_cluster.ecs_cluster_name} --service ${module.app_cluster.ecs_service_name} --force-new-deployment --region ${var.aws_region}

    3. Build and deploy frontend:
       cd ../../patient-aws/frontend
       NEXT_PUBLIC_API_URL=http://${module.app_cluster.alb_dns_name} npm run build
       aws s3 sync out/ s3://${module.static_site.s3_bucket_name}/ --delete
       aws cloudfront create-invalidation --distribution-id ${module.static_site.cloudfront_distribution_id} --paths "/*"

    🌐 Access URLs:
       Backend API: http://${module.app_cluster.alb_dns_name}
       Frontend:    https://${module.static_site.cloudfront_domain_name}

    📊 Monitoring:
       CloudWatch Logs: /ecs/${var.prefix}
       ECS Console: https://console.aws.amazon.com/ecs/v2/clusters/${module.app_cluster.ecs_cluster_name}

  EOT
}
