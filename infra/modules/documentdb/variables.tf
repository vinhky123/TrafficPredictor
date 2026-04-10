variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "allowed_sg_ids" {
  description = "Security groups allowed to connect to DocumentDB"
  type        = list(string)
}

variable "instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "master_username" {
  type = string
}

variable "master_password" {
  type      = string
  sensitive = true
}
