variable "prefix" {}
variable "vpc_id" {}
variable "public_subnet_ids" {}
variable "private_subnet_ids" {}
variable "container_port" {}
variable "task_cpu" {}
variable "task_memory" {}
variable "desired_count" {}

# Database info
variable "db_host" {}
variable "db_port" {}
variable "db_name" {}
variable "db_user" {}
variable "db_password" {}
variable "jwt_secret" {}

# SSL / Domain
variable "certificate_arn" {
  type    = string
  default = ""
}
variable "enable_https" {
  type    = bool
  default = false
}
variable "domain_name" {
  type    = string
  default = ""
}

variable "zone_id" {
  type    = string
  default = ""
}
