variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Deployment environment (dev / prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project identifier used in resource naming"
  type        = string
  default     = "traffic-predictor"
}

# ── Networking ────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AZs to distribute subnets across"
  type        = list(string)
  default     = ["ap-southeast-1a", "ap-southeast-1b"]
}

# ── ECS / Backend ─────────────────────────────────────────────────────────

variable "backend_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "Fargate task memory (MiB)"
  type        = number
  default     = 2048
}

variable "backend_desired_count" {
  description = "Number of backend tasks to run"
  type        = number
  default     = 1
}

# ── DocumentDB ────────────────────────────────────────────────────────────

variable "docdb_instance_class" {
  description = "DocumentDB instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "docdb_master_username" {
  description = "DocumentDB master username"
  type        = string
  default     = "trafficadmin"
}

variable "docdb_master_password" {
  description = "DocumentDB master password"
  type        = string
  sensitive   = true
}

# ── MWAA ──────────────────────────────────────────────────────────────────

variable "mwaa_environment_class" {
  description = "MWAA environment class"
  type        = string
  default     = "mw1.small"
}

variable "here_api_key" {
  description = "HERE Traffic Flow API key (stored as Airflow Variable)"
  type        = string
  sensitive   = true
  default     = ""
}
