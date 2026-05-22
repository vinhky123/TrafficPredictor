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

# ── HERE API ──────────────────────────────────────────────────────────────

variable "here_api_key" {
  description = "HERE Traffic Flow API key"
  type        = string
  sensitive   = true
  default     = ""
}
