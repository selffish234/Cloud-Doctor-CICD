# ========================================
# AWS Client VPN Endpoint Module
# ========================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 4.0"
    }
  }
}

# ----------------------------------------
# 1. Automated Certificate Generation
# ----------------------------------------

# CA Key & Certificate
resource "tls_private_key" "ca" {
  algorithm = "RSA"
}

resource "tls_self_signed_cert" "ca" {
  private_key_pem = tls_private_key.ca.private_key_pem

  subject {
    common_name  = "ca.cvpn.local"
    organization = "Cloud Doctor"
  }


  validity_period_hours = 87600 # 10 years
  is_ca_certificate     = true

  allowed_uses = [
    "cert_signing",
    "crl_signing",
  ]
}

# Server Key & Certificate
resource "tls_private_key" "server" {
  algorithm = "RSA"
}

resource "tls_cert_request" "server" {
  private_key_pem = tls_private_key.server.private_key_pem

  subject {
    common_name  = "server.cvpn.local"
    organization = "Cloud Doctor"
  }

}

resource "tls_locally_signed_cert" "server" {
  cert_request_pem   = tls_cert_request.server.cert_request_pem
  ca_private_key_pem = tls_private_key.ca.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.ca.cert_pem

  validity_period_hours = 87600

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

# Client Key & Certificate (for the user)
resource "tls_private_key" "client" {
  algorithm = "RSA"
}

resource "tls_cert_request" "client" {
  private_key_pem = tls_private_key.client.private_key_pem

  subject {
    common_name  = "client1.cvpn.local"
    organization = "Cloud Doctor"
  }

}

resource "tls_locally_signed_cert" "client" {
  cert_request_pem   = tls_cert_request.client.cert_request_pem
  ca_private_key_pem = tls_private_key.ca.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.ca.cert_pem

  validity_period_hours = 87600

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "client_auth",
  ]
}

# Import Certs to ACM
resource "aws_acm_certificate" "server_v2" {
  private_key      = tls_private_key.server.private_key_pem
  certificate_body = tls_locally_signed_cert.server.cert_pem
  certificate_chain = tls_self_signed_cert.ca.cert_pem

  tags = {
    Name = "${var.prefix}-vpn-server-cert-v2"
  }
}


resource "aws_acm_certificate" "client" {
  private_key      = tls_private_key.client.private_key_pem
  certificate_body = tls_locally_signed_cert.client.cert_pem
  certificate_chain = tls_self_signed_cert.ca.cert_pem

  tags = {
    Name = "${var.prefix}-vpn-client-cert"
  }
}

# ----------------------------------------
# 2. Client VPN Endpoint
# ----------------------------------------

resource "aws_ec2_client_vpn_endpoint" "this" {
  description            = "Cloud Doctor Client VPN"
  server_certificate_arn = aws_acm_certificate.server_v2.arn
  client_cidr_block      = var.vpn_cidr

  split_tunnel           = true
  transport_protocol     = "udp"

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = aws_acm_certificate.client.arn
  }

  connection_log_options {
    enabled = false
  }

  tags = {
    Name = "${var.prefix}-vpn-endpoint"
  }
}

# ----------------------------------------
# 3. Network Association & Authorization
# ----------------------------------------

resource "aws_ec2_client_vpn_network_association" "this" {
  count                  = length(var.private_subnet_ids)
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.this.id
  subnet_id              = var.private_subnet_ids[count.index]
}

resource "aws_ec2_client_vpn_authorization_rule" "this" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.this.id
  target_network_cidr    = var.vpc_cidr
  authorize_all_groups   = true
  description            = "Allow access to VPC"
}

# ----------------------------------------
# 4. Security Group for VPN Interface
# ----------------------------------------
# AWS creates ENIs in your VPC. We need a security group for them.

resource "aws_security_group" "vpn" {
  name        = "${var.prefix}-vpn-sg"
  description = "Security group for Client VPN ENIs"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # Required for VPN to function properly (inbound from VPN clients)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.prefix}-vpn-sg"
  }
}

# Apply this SG to the VPN Endpoint (Not directly supported in Terraform resource argument efficiently, 
# but usually AWS assigns the default VPC security group. 
# Best practice is to rely on Authorization Rules for access control inside VPN, 
# and use the VPN's SG to control what the VPN *ENIs* can talk to in the VPC.)
