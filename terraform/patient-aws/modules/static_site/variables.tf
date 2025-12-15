variable "prefix" {}
variable "bucket_name" {}
variable "alb_dns_name" {}

# SSL / Domain
variable "certificate_arn" {
  type    = string
  default = ""
}
variable "domain_name" {
  type    = string
  default = ""
}
variable "zone_id" {
  type    = string
  default = ""
}
