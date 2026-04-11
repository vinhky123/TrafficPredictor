variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnets" {
  type = list(string)
}

variable "dag_s3_bucket" {
  type = string
}

variable "environment_class" {
  type    = string
  default = "mw1.small"
}

variable "dynamodb_arn" {
  type = string
}

variable "dynamodb_gsi_arn" {
  type = string
}
