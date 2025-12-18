/**
 * Cloud Doctor - Monitoring Module Outputs
 */

output "sns_topic_arn" {
  description = "CloudWatch 알람용 SNS Topic ARN"
  value       = aws_sns_topic.alarm_topic.arn
}

output "sns_topic_name" {
  description = "SNS Topic 이름"
  value       = aws_sns_topic.alarm_topic.name
}

output "lambda_function_name" {
  description = "Doctor Trigger Lambda 함수 이름"
  value       = aws_lambda_function.doctor_trigger.function_name
}

output "lambda_function_arn" {
  description = "Doctor Trigger Lambda 함수 ARN"
  value       = aws_lambda_function.doctor_trigger.arn
}

output "error_alarm_arn" {
  description = "에러 로그 알람 ARN"
  value       = aws_cloudwatch_metric_alarm.error_alarm.arn
}

output "error_alarm_name" {
  description = "에러 로그 알람 이름"
  value       = aws_cloudwatch_metric_alarm.error_alarm.alarm_name
}

output "alarm_names" {
  description = "생성된 모든 알람 이름 목록"
  value = compact([
    aws_cloudwatch_metric_alarm.error_alarm.alarm_name,
    length(aws_cloudwatch_metric_alarm.ecs_cpu_alarm) > 0 ? aws_cloudwatch_metric_alarm.ecs_cpu_alarm[0].alarm_name : "",
    length(aws_cloudwatch_metric_alarm.ecs_memory_alarm) > 0 ? aws_cloudwatch_metric_alarm.ecs_memory_alarm[0].alarm_name : "",
    length(aws_cloudwatch_metric_alarm.alb_5xx_alarm) > 0 ? aws_cloudwatch_metric_alarm.alb_5xx_alarm[0].alarm_name : "",
    length(aws_cloudwatch_metric_alarm.rds_cpu_alarm) > 0 ? aws_cloudwatch_metric_alarm.rds_cpu_alarm[0].alarm_name : "",
  ])
}
