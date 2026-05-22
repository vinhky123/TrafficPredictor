variable "name" {
  type = string
}

variable "definition" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "type" {
  type    = string
  default = "STANDARD"
}
