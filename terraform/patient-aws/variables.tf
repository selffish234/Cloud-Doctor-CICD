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
  default     = "db.t3.micro"
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

variable "enable_vpn" {
  description = "Enable AWS Client VPN"
  type        = bool
  default     = true
}

