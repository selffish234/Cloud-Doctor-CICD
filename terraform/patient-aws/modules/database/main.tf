# ========================================
# Security Group for RDS
# ========================================
resource "aws_security_group" "db" {
  name        = "${var.prefix}-db-sg"
  description = "Security group for RDS MySQL - allows access from app tier only"
  vpc_id      = var.vpc_id

  ingress {
    description = "MySQL from VPC"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.prefix}-db-sg"
    Project = "CloudDoctor"
    Tier    = "Database"
  }
}

# ========================================
# RDS MySQL Instance
# ========================================
resource "aws_db_instance" "this" {
  identifier     = "${var.prefix}-mysql"
  engine         = "mysql"
  engine_version = "8.0"

  instance_class    = var.db_instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  multi_az               = var.multi_az
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = [aws_security_group.db.id]

  # Backup settings
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Performance Insights for Doctor Zone monitoring
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Deletion protection for production
  skip_final_snapshot       = true
  final_snapshot_identifier = "${var.prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  deletion_protection       = false

  # Parameter group for optimized settings
  parameter_group_name = aws_db_parameter_group.this.name

  tags = {
    Name    = "${var.prefix}-mysql"
    Project = "CloudDoctor"
    Tier    = "Database"
  }
}

# ========================================
# DB Parameter Group (Optimized for monitoring)
# ========================================
resource "aws_db_parameter_group" "this" {
  name   = "${var.prefix}-mysql-params"
  family = "mysql8.0"

  # Enable slow query log for chaos scenario detection
  parameter {
    name  = "slow_query_log"
    value = "1"
  }

  parameter {
    name  = "long_query_time"
    value = "2"
  }

  parameter {
    name  = "log_queries_not_using_indexes"
    value = "1"
  }

  # Connection settings
  parameter {
    name  = "max_connections"
    value = "150"
  }

  tags = {
    Name    = "${var.prefix}-mysql-params"
    Project = "CloudDoctor"
  }
}
