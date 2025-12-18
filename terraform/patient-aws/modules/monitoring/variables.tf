/**
 * Cloud Doctor - Monitoring Module Variables
 */

# ============================================================
# Required Variables
# ============================================================

variable "prefix" {
  description = "리소스 이름 접두사"
  type        = string
}

variable "log_group_name" {
  description = "모니터링할 CloudWatch Log Group 이름"
  type        = string
}

variable "doctor_zone_url" {
  description = "GCP Cloud Run Doctor Zone URL (예: https://doctor-zone-xxx.run.app)"
  type        = string
}

# ============================================================
# Optional Variables - Thresholds
# ============================================================

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "error_threshold" {
  description = "5분간 에러 로그 개수 임계값"
  type        = number
  default     = 10
}

variable "cpu_threshold" {
  description = "ECS CPU 사용률 임계값 (%)"
  type        = number
  default     = 80
}

variable "memory_threshold" {
  description = "ECS 메모리 사용률 임계값 (%)"
  type        = number
  default     = 80
}

variable "alb_5xx_threshold" {
  description = "5분간 ALB 5xx 에러 개수 임계값"
  type        = number
  default     = 10
}

variable "rds_cpu_threshold" {
  description = "RDS CPU 사용률 임계값 (%)"
  type        = number
  default     = 80
}

# ============================================================
# Optional Variables - Resource References
# ============================================================

variable "ecs_cluster_name" {
  description = "ECS 클러스터 이름 (CPU/메모리 알람용)"
  type        = string
  default     = ""
}

variable "ecs_service_name" {
  description = "ECS 서비스 이름 (CPU/메모리 알람용)"
  type        = string
  default     = ""
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix (5xx 알람용, 예: app/my-alb/xxxxx)"
  type        = string
  default     = ""
}

variable "rds_instance_id" {
  description = "RDS 인스턴스 ID (CPU 알람용)"
  type        = string
  default     = ""
}

# ============================================================
# Optional Variables - Notifications
# ============================================================

variable "slack_webhook_url" {
  description = "Slack Webhook URL (Doctor Zone 실패 시 백업 알림)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alarm_email" {
  description = "알람 수신 이메일 (선택사항)"
  type        = string
  default     = ""
}
