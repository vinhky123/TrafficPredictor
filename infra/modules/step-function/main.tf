resource "aws_sfn_state_machine" "this" {
  name     = var.name
  role_arn = var.role_arn
  type     = var.type

  definition = var.definition
}
