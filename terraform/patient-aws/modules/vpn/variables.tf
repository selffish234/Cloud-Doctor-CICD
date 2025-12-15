variable "prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "vpn_cidr" {
  description = "CIDR block for VPN clients (must not overlap with VPC)"
  type        = string
  default     = "10.100.0.0/22"
}
