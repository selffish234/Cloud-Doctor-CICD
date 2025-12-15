# ========================================
# VPC
# ========================================
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "${var.prefix}-vpc"
    Project = "CloudDoctor"
  }
}

# ========================================
# Internet Gateway
# ========================================
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name    = "${var.prefix}-igw"
    Project = "CloudDoctor"
  }
}

# ========================================
# Public Subnets
# ========================================
resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name    = "${var.prefix}-public-${count.index + 1}"
    Type    = "Public"
    Project = "CloudDoctor"
  }
}

# ========================================
# Private App Subnets
# ========================================
resource "aws_subnet" "private" {
  count             = length(var.private_subnets)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.azs[count.index]

  tags = {
    Name    = "${var.prefix}-private-app-${count.index + 1}"
    Type    = "Private"
    Tier    = "Application"
    Project = "CloudDoctor"
  }
}

# ========================================
# Private Database Subnets
# ========================================
resource "aws_subnet" "database" {
  count             = length(var.database_subnets)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.database_subnets[count.index]
  availability_zone = var.azs[count.index]

  tags = {
    Name    = "${var.prefix}-private-db-${count.index + 1}"
    Type    = "Private"
    Tier    = "Database"
    Project = "CloudDoctor"
  }
}

# ========================================
# NAT Gateway (High Availability)
# ========================================
resource "aws_eip" "nat" {
  count  = length(var.public_subnets)
  domain = "vpc"

  tags = {
    Name    = "${var.prefix}-nat-eip-${count.index + 1}"
    Project = "CloudDoctor"
  }
}

resource "aws_nat_gateway" "this" {
  count         = length(var.public_subnets)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name    = "${var.prefix}-nat-${count.index + 1}"
    Project = "CloudDoctor"
  }

  depends_on = [aws_internet_gateway.this]
}

# ========================================
# Route Tables - Public
# ========================================
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name    = "${var.prefix}-rt-public"
    Project = "CloudDoctor"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ========================================
# Route Tables - Private (per AZ for HA)
# ========================================
resource "aws_route_table" "private" {
  count  = length(var.private_subnets)
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this[count.index].id
  }

  tags = {
    Name    = "${var.prefix}-rt-private-${count.index + 1}"
    Project = "CloudDoctor"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# ========================================
# DB Subnet Group (for RDS)
# ========================================
resource "aws_db_subnet_group" "this" {
  name       = "${var.prefix}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = {
    Name    = "${var.prefix}-db-subnet-group"
    Project = "CloudDoctor"
  }
}
