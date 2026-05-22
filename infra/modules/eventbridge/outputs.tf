output "rule_arn" {
  value = aws_cloudwatch_event_rule.this.arn
}

output "rule_name" {
  value = aws_cloudwatch_event_rule.this.name
}
