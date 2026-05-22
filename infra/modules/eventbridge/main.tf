resource "aws_cloudwatch_event_rule" "this" {
  name                = var.name
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "this" {
  rule      = aws_cloudwatch_event_rule.this.name
  arn       = var.target_arn
  role_arn  = var.target_role_arn
}
