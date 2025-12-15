output "endpoint" {
  description = "RDS endpoint (including port)"
  value       = aws_db_instance.this.endpoint
}

output "address" {
  description = "RDS address (hostname only)"
  value       = aws_db_instance.this.address
}

output "port" {
  description = "RDS port"
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.this.db_name
}

output "security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.db.id
}
