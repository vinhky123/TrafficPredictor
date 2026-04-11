output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "backend_alb_dns" {
  description = "DNS name of the backend ALB"
  value       = module.ecs.alb_dns_name
}

output "backend_ecr_repo" {
  description = "ECR repository URL for the backend image"
  value       = module.ecr.backend_repo_url
}

output "airflow_ecr_repo" {
  description = "ECR repository URL for the Airflow image"
  value       = module.ecr.airflow_repo_url
}

output "documentdb_endpoint" {
  description = "DocumentDB cluster endpoint"
  value       = module.documentdb.endpoint
}

output "data_bucket" {
  description = "S3 bucket for ETL data (raw + transformed)"
  value       = module.s3.data_bucket_name
}

output "mwaa_webserver_url" {
  description = "MWAA Airflow webserver URL"
  value       = module.mwaa.webserver_url
}

output "dynamodb_table" {
  description = "DynamoDB road segments table name"
  value       = module.dynamodb.table_name
}
