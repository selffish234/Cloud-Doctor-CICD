# ========================================
# General Variables
# ========================================
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "patient-zone"
}

# ========================================
# Network Variables
# ========================================
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

# ========================================
# Database Variables
# ========================================
variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large"
}

variable "db_multi_az" {
  description = "Enable RDS multi-AZ deployment"
  type        = bool
  default     = false
}

# ========================================
# Application Variables
# ========================================
variable "jwt_secret" {
  description = "JWT secret for authentication"
  type        = string
  sensitive   = true
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

# ========================================
# Frontend Variables
# ========================================
variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend (must be globally unique)"
  type        = string
  default     = "cloud-doctor-patient-frontend"
}

# ========================================
# Domain & SSL Variables
# ========================================
variable "domain_name" {
  description = "Root domain name (e.g., example.com)"
  type        = string
  default     = "" # Optional: Leave empty if not using custom domain
}



# ========================================
# Monitoring Variables (Auto-Trigger)
# ========================================
variable "enable_monitoring" {
  description = "Enable CloudWatch Alarm + Lambda auto-trigger for Doctor Zone"
  type        = bool
  default     = false
}

variable "doctor_zone_url" {
  description = "GCP Cloud Run Doctor Zone URL (예: https://doctor-zone-xxx.run.app)"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack Webhook URL for fallback notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alarm_email" {
  description = "Email address for alarm notifications (optional)"
  type        = string
  default     = ""
}

# Alarm Thresholds
variable "alarm_error_threshold" {
  description = "Error count threshold (5분간)"
  type        = number
  default     = 10
}

variable "alarm_cpu_threshold" {
  description = "ECS CPU usage threshold (%)"
  type        = number
  default     = 80
}

variable "alarm_memory_threshold" {
  description = "ECS Memory usage threshold (%)"
  type        = number
  default     = 80
}

variable "alarm_5xx_threshold" {
  description = "ALB 5xx error count threshold (5분간)"
  type        = number
  default     = 10
}

variable "alarm_rds_cpu_threshold" {
  description = "RDS CPU usage threshold (%)"
  type        = number
  default     = 80
}

