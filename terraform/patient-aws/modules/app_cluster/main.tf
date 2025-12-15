# ========================================
# Security Group - ALB
# ========================================
resource "aws_security_group" "alb" {
  name        = "${var.prefix}-alb-sg"
  description = "Security group for public ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.prefix}-alb-sg"
    Project = "CloudDoctor"
    Tier    = "Web"
  }
}

# ========================================
# Security Group - ECS Tasks
# ========================================
resource "aws_security_group" "ecs" {
  name        = "${var.prefix}-ecs-sg"
  description = "Security group for ECS tasks - allows traffic from ALB only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Container port from ALB"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.prefix}-ecs-sg"
    Project = "CloudDoctor"
    Tier    = "Application"
  }
}

# ========================================
# Application Load Balancer
# ========================================
resource "aws_lb" "this" {
  name               = "${var.prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false
  enable_http2               = true

  tags = {
    Name    = "${var.prefix}-alb"
    Project = "CloudDoctor"
    Tier    = "Web"
  }
}

# ========================================
# Target Group
# ========================================
resource "aws_lb_target_group" "this" {
  name        = "${var.prefix}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name    = "${var.prefix}-tg"
    Project = "CloudDoctor"
  }
}

# ========================================
# ALB Listener - HTTP
# ========================================
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = var.enable_https ? "redirect" : "forward"
    
    # Conditional redirect block
    dynamic "redirect" {
      for_each = var.enable_https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    # Conditional forward block
    target_group_arn = !var.enable_https ? aws_lb_target_group.this.arn : null
  }


  tags = {
    Name    = "${var.prefix}-listener-http"
    Project = "CloudDoctor"
  }
}

# ========================================
# ALB Listener - HTTPS
# ========================================
resource "aws_lb_listener" "https" {
  count             = var.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn

  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  tags = {
    Name    = "${var.prefix}-listener-https"
    Project = "CloudDoctor"
  }
}


# ========================================
# CloudWatch Log Group
# ========================================
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.prefix}"
  retention_in_days = 7

  tags = {
    Name    = "${var.prefix}-logs"
    Project = "CloudDoctor"
  }
}

# ========================================
# ECR Repository
# ========================================
resource "aws_ecr_repository" "backend" {
  name         = "${var.prefix}-backend"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "${var.prefix}-backend-repo"
    Project = "CloudDoctor"
  }
}

# ========================================
# ECS Cluster
# ========================================
resource "aws_ecs_cluster" "this" {
  name = "${var.prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name    = "${var.prefix}-cluster"
    Project = "CloudDoctor"
  }
}

# ========================================
# IAM Role - ECS Task Execution
# ========================================
resource "aws_iam_role" "execution" {
  name = "${var.prefix}-ecs-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name    = "${var.prefix}-ecs-exec-role"
    Project = "CloudDoctor"
  }
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ========================================
# IAM Role - ECS Task
# ========================================
resource "aws_iam_role" "task" {
  name = "${var.prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name    = "${var.prefix}-ecs-task-role"
    Project = "CloudDoctor"
  }
}

# Allow task to write logs
resource "aws_iam_role_policy" "task_logs" {
  name = "${var.prefix}-task-logs-policy"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "${aws_cloudwatch_log_group.ecs.arn}:*"
    }]
  })
}

# ========================================
# ECS Task Definition
# ========================================
resource "aws_ecs_task_definition" "this" {
  family                   = "${var.prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${aws_ecr_repository.backend.repository_url}:latest"
    essential = true

    environment = [
      { name = "NODE_ENV", value = "production" },
      { name = "DB_HOST", value = var.db_host },
      { name = "DB_PORT", value = var.db_port },
      { name = "DB_NAME", value = var.db_name },
      { name = "DB_USER", value = var.db_user },
      { name = "DB_PASSWORD", value = var.db_password },
      { name = "JWT_SECRET", value = var.jwt_secret },
      { name = "CHAOS_MODE", value = "false" }
    ]

    portMappings = [{
      containerPort = var.container_port
      hostPort      = var.container_port
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])

  tags = {
    Name    = "${var.prefix}-task"
    Project = "CloudDoctor"
  }
}

# ========================================
# ECS Service
# ========================================
resource "aws_ecs_service" "this" {
  name            = "${var.prefix}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "backend"
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_listener.http
  ]

  tags = {
    Name    = "${var.prefix}-service"
    Project = "CloudDoctor"
  }
}

# ========================================
# Data Sources
# ========================================
data "aws_region" "current" {}
