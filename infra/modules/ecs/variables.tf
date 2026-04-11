variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnets" {
  type = list(string)
}

variable "private_subnets" {
  type = list(string)
}

variable "ecr_repo_url" {
  type = string
}

variable "cpu" {
  type    = number
  default = 1024
}

variable "memory" {
  type    = number
  default = 2048
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "mongodb_uri" {
  type      = string
  sensitive = true
}

variable "dynamodb_table" {
  type = string
}

variable "dynamodb_arn" {
  type = string
}

variable "dynamodb_gsi_arn" {
  type = string
}
