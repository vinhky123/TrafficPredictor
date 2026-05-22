variable "name" {
  type = string
}

variable "schedule_expression" {
  type = string
}

variable "target_arn" {
  type = string
}

variable "target_role_arn" {
  type    = string
  default = null
}
