/**
 * Cloud Doctor - Auto-Trigger Monitoring Module
 *
 * CloudWatch Alarm -> SNS -> Lambda -> GCP Cloud Run (Doctor Zone)
 *
 * 이 모듈은 Patient Zone의 에러를 자동으로 감지하고
 * Doctor Zone을 호출하여 AI 분석을 트리거합니다.
 */

# ============================================================
# Data Sources
# ============================================================

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Lambda 코드 ZIP 파일 생성
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_function.zip"
}

# ============================================================
# SNS Topic - 알람 수신 및 Lambda 트리거
# ============================================================

resource "aws_sns_topic" "alarm_topic" {
  name = "${var.prefix}-cloudwatch-alarms"

  tags = {
    Name        = "${var.prefix}-cloudwatch-alarms"
    Environment = var.environment
    Purpose     = "CloudWatch Alarm notifications"
  }
}

# SNS Topic Policy - CloudWatch가 SNS에 게시할 수 있도록 허용
resource "aws_sns_topic_policy" "alarm_topic_policy" {
  arn = aws_sns_topic.alarm_topic.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudWatchAlarms"
        Effect    = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.alarm_topic.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = "arn:aws:cloudwatch:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:alarm:*"
          }
        }
      }
    ]
  })
}

# ============================================================
# CloudWatch Metric Filter - 에러 로그를 메트릭으로 변환
# ============================================================

resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${var.prefix}-error-count"
  pattern        = "?ERROR ?Error ?error ?CRITICAL ?FATAL ?Exception"
  log_group_name = var.log_group_name

  metric_transformation {
    name          = "ErrorCount"
    namespace     = "${var.prefix}/ApplicationLogs"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "warning_count" {
  name           = "${var.prefix}-warning-count"
  pattern        = "?WARNING ?Warning ?warning ?WARN"
  log_group_name = var.log_group_name

  metric_transformation {
    name          = "WarningCount"
    namespace     = "${var.prefix}/ApplicationLogs"
    value         = "1"
    default_value = "0"
  }
}

# ============================================================
# CloudWatch Alarms - 임계값 초과 시 SNS로 알림
# ============================================================

# 에러 로그 알람 - 5분간 에러 10개 이상
resource "aws_cloudwatch_metric_alarm" "error_alarm" {
  alarm_name          = "${var.prefix}-error-spike"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "ErrorCount"
  namespace           = "${var.prefix}/ApplicationLogs"
  period              = 300  # 5분
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "Patient Zone에서 ${var.error_threshold}개 이상의 에러가 5분 내에 발생했습니다."
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alarm_topic.arn]
  ok_actions    = [aws_sns_topic.alarm_topic.arn]

  tags = {
    Name        = "${var.prefix}-error-spike"
    Environment = var.environment
    Severity    = "critical"
  }
}

# ECS CPU 사용률 알람
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_alarm" {
  count = var.ecs_cluster_name != "" ? 1 : 0

  alarm_name          = "${var.prefix}-ecs-high-cpu"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_threshold
  alarm_description   = "ECS 서비스 CPU 사용률이 ${var.cpu_threshold}%를 초과했습니다."
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [aws_sns_topic.alarm_topic.arn]
  ok_actions    = [aws_sns_topic.alarm_topic.arn]

  tags = {
    Name        = "${var.prefix}-ecs-high-cpu"
    Environment = var.environment
    Severity    = "warning"
  }
}

# ECS 메모리 사용률 알람
resource "aws_cloudwatch_metric_alarm" "ecs_memory_alarm" {
  count = var.ecs_cluster_name != "" ? 1 : 0

  alarm_name          = "${var.prefix}-ecs-high-memory"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.memory_threshold
  alarm_description   = "ECS 서비스 메모리 사용률이 ${var.memory_threshold}%를 초과했습니다."
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [aws_sns_topic.alarm_topic.arn]
  ok_actions    = [aws_sns_topic.alarm_topic.arn]

  tags = {
    Name        = "${var.prefix}-ecs-high-memory"
    Environment = var.environment
    Severity    = "warning"
  }
}

# ALB 5xx 에러 알람
resource "aws_cloudwatch_metric_alarm" "alb_5xx_alarm" {
  count = var.alb_arn_suffix != "" ? 1 : 0

  alarm_name          = "${var.prefix}-alb-5xx-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = var.alb_5xx_threshold
  alarm_description   = "ALB에서 5xx 에러가 ${var.alb_5xx_threshold}개 이상 발생했습니다."
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarm_topic.arn]
  ok_actions    = [aws_sns_topic.alarm_topic.arn]

  tags = {
    Name        = "${var.prefix}-alb-5xx-errors"
    Environment = var.environment
    Severity    = "critical"
  }
}

# RDS CPU 사용률 알람
resource "aws_cloudwatch_metric_alarm" "rds_cpu_alarm" {
  count = var.rds_instance_id != "" ? 1 : 0

  alarm_name          = "${var.prefix}-rds-high-cpu"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.rds_cpu_threshold
  alarm_description   = "RDS CPU 사용률이 ${var.rds_cpu_threshold}%를 초과했습니다."
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alarm_topic.arn]
  ok_actions    = [aws_sns_topic.alarm_topic.arn]

  tags = {
    Name        = "${var.prefix}-rds-high-cpu"
    Environment = var.environment
    Severity    = "warning"
  }
}

# ============================================================
# Lambda Function - Doctor Zone 호출
# ============================================================

# Lambda IAM Role
resource "aws_iam_role" "lambda_role" {
  name = "${var.prefix}-doctor-trigger-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.prefix}-doctor-trigger-lambda-role"
    Environment = var.environment
  }
}

# Lambda 기본 실행 권한 (CloudWatch Logs 쓰기)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function
resource "aws_lambda_function" "doctor_trigger" {
  function_name = "${var.prefix}-doctor-trigger"
  description   = "CloudWatch Alarm 발생 시 GCP Cloud Run Doctor Zone을 호출합니다."

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  handler          = "trigger_doctor.lambda_handler"
  runtime          = "python3.11"
  timeout          = 120  # 2분 (Doctor Zone 응답 대기)
  memory_size      = 256

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      DOCTOR_ZONE_URL   = var.doctor_zone_url
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }

  tags = {
    Name        = "${var.prefix}-doctor-trigger"
    Environment = var.environment
  }
}

# SNS -> Lambda 권한
resource "aws_lambda_permission" "sns_trigger" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.doctor_trigger.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alarm_topic.arn
}

# SNS Subscription - Lambda
resource "aws_sns_topic_subscription" "lambda_subscription" {
  topic_arn = aws_sns_topic.alarm_topic.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.doctor_trigger.arn
}

# ============================================================
# Optional: Email Subscription
# ============================================================

resource "aws_sns_topic_subscription" "email_subscription" {
  count = var.alarm_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alarm_topic.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
