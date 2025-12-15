# ========================================
# Terraform Configuration
# ========================================
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment for remote state
  # backend "s3" {
  #   bucket         = "cloud-doctor-tfstate"
  #   key            = "patient-aws/terraform.tfstate"
  #   region         = "ap-northeast-2"
  #   dynamodb_table = "cloud-doctor-tflock"
  #   encrypt        = true
  # }
}

# ========================================
# Provider Configuration
# ========================================
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CloudDoctor"
      Environment = "Production"
      ManagedBy   = "Terraform"
      Zone        = "Patient"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  
  default_tags {
    tags = {
      Project     = "CloudDoctor"
      Environment = "Production"
      ManagedBy   = "Terraform"
      Zone        = "Patient"
    }
  }
}


# ========================================
# Local Variables
# ========================================
locals {
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets  = ["10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.21.0/24", "10.0.22.0/24"]
}

# ========================================
# Domain & SSL (Route53 + ACM)
# ========================================
data "aws_route53_zone" "this" {
  count = var.domain_name != "" ? 1 : 0
  name  = var.domain_name
}

resource "aws_acm_certificate" "this" {
  count       = var.domain_name != "" ? 1 : 0
  domain_name = "*.${var.domain_name}"
  
  subject_alternative_names = [var.domain_name]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.prefix}-wildcard-cert"
  }
}

# DNS Validation Record
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.this[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.this[0].zone_id
}

resource "aws_acm_certificate_validation" "this" {
  count                   = var.domain_name != "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.this[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Certificate for CloudFront (Must be in us-east-1)
resource "aws_acm_certificate" "cloudfront" {
  count       = var.domain_name != "" ? 1 : 0
  provider    = aws.us_east_1
  domain_name = "patient.${var.domain_name}"
  
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.prefix}-cloudfront-cert"
  }
}

# CloudFront DNS Validation (in original region Route53)
resource "aws_route53_record" "cloudfront_cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.cloudfront[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.this[0].zone_id
}

resource "aws_acm_certificate_validation" "cloudfront" {
  count                   = var.domain_name != "" ? 1 : 0
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cloudfront[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cloudfront_cert_validation : record.fqdn]
}



# ========================================
# Network Module
# ========================================
module "network" {
  source = "./modules/network"

  prefix           = var.prefix
  vpc_cidr         = var.vpc_cidr
  public_subnets   = local.public_subnets
  private_subnets  = local.private_subnets
  database_subnets = local.database_subnets
  azs              = var.availability_zones
}

# ========================================
# Database Module
# ========================================
module "database" {
  source = "./modules/database"

  prefix               = var.prefix
  vpc_id               = module.network.vpc_id
  vpc_cidr             = module.network.vpc_cidr
  db_subnet_group_name = module.network.db_subnet_group_name
  db_name              = "patient_db"
  db_username          = "admin"
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  multi_az             = var.db_multi_az
}

# ========================================
# Application Cluster Module
# ========================================
module "app_cluster" {
  source = "./modules/app_cluster"

  prefix             = var.prefix
  vpc_id             = module.network.vpc_id
  public_subnet_ids  = module.network.public_subnet_ids
  private_subnet_ids = module.network.private_subnet_ids

  container_port = 3000
  task_cpu       = 256
  task_memory    = 512
  desired_count  = var.ecs_desired_count

  # Database connection
  db_host     = module.database.address
  db_port     = tostring(module.database.port)
  db_name     = module.database.db_name
  db_user     = "admin"
  db_password = var.db_password
  jwt_secret  = var.jwt_secret

  depends_on = [module.database]

  # SSL Configuration
  certificate_arn = var.domain_name != "" ? aws_acm_certificate.this[0].arn : ""
  domain_name     = var.domain_name
  zone_id         = var.domain_name != "" ? data.aws_route53_zone.this[0].zone_id : ""
  enable_https    = var.domain_name != ""
}


resource "aws_route53_record" "alb" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.this[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.app_cluster.alb_dns_name
    zone_id                = module.app_cluster.alb_zone_id
    evaluate_target_health = true
  }
}


# ========================================
# Static Site Module (Frontend)
# ========================================
module "static_site" {
  source = "./modules/static_site"

  prefix       = var.prefix
  bucket_name  = var.frontend_bucket_name
  alb_dns_name = module.app_cluster.alb_dns_name
  
  # Custom Domain
  domain_name     = var.domain_name != "" ? "patient.${var.domain_name}" : ""
  certificate_arn = var.domain_name != "" ? aws_acm_certificate.cloudfront[0].arn : ""
  zone_id         = var.domain_name != "" ? data.aws_route53_zone.this[0].zone_id : ""
}


# ========================================
# Client VPN Module
# ========================================
module "vpn" {
  source = "./modules/vpn"
  count  = var.enable_vpn ? 1 : 0

  prefix             = var.prefix
  vpc_id             = module.network.vpc_id
  vpc_cidr           = module.network.vpc_cidr
  private_subnet_ids = module.network.private_subnet_ids
}

