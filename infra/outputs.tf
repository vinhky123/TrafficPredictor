# ── Networking ────────────────────────────────────────────────────────────

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

# ── ECR ───────────────────────────────────────────────────────────────────

output "predict_ecr_repo" {
  description = "ECR repository URL for the predict Lambda container image"
  value       = module.ecr.predict_repo_url
}

# ── S3 ────────────────────────────────────────────────────────────────────

output "raw_bucket" {
  description = "S3 bucket for raw HERE API data"
  value       = module.s3.raw_bucket_name
}

output "processed_bucket" {
  description = "S3 bucket for transformed JSONL data"
  value       = module.s3.processed_bucket_name
}

output "lambdas_bucket" {
  description = "S3 bucket for Lambda deployment zips"
  value       = module.s3.lambdas_bucket_name
}

output "models_bucket" {
  description = "S3 bucket for model artifacts"
  value       = module.s3.models_bucket_name
}

# ── DynamoDB ──────────────────────────────────────────────────────────────

output "segments_table" {
  description = "DynamoDB road segments table name"
  value       = module.dynamodb.segments_table_name
}

output "speeds_table" {
  description = "DynamoDB speeds table name"
  value       = module.dynamodb.speeds_table_name
}

output "predictions_table" {
  description = "DynamoDB predictions table name"
  value       = module.dynamodb.predictions_table_name
}

output "connections_table" {
  description = "DynamoDB WebSocket connections table name"
  value       = module.dynamodb.connections_table_name
}

# ── API Gateway ───────────────────────────────────────────────────────────

output "api_gateway_url" {
  description = "REST API Gateway invoke URL"
  value       = module.api_gateway.api_url
}

# ── SSE API ───────────────────────────────────────────────────────────────

output "sse_url" {
  description = "SSE API Gateway invoke URL"
  value       = module.sse_api.sse_url
}

# ── Step Function ─────────────────────────────────────────────────────────

output "step_function_arn" {
  description = "ETL pipeline Step Function ARN"
  value       = module.step_function.state_machine_arn
}

# ── Lambda Functions ──────────────────────────────────────────────────────

output "lambda_api_arn" {
  description = "REST API Lambda function ARN"
  value       = module.lambda_api.function_arn
}

output "lambda_extract_arn" {
  description = "Extract Lambda function ARN"
  value       = module.lambda_extract.function_arn
}

output "lambda_transform_arn" {
  description = "Transform Lambda function ARN"
  value       = module.lambda_transform.function_arn
}

output "lambda_load_arn" {
  description = "Load Lambda function ARN"
  value       = module.lambda_load.function_arn
}

output "lambda_notify_arn" {
  description = "Notify Lambda function ARN"
  value       = module.lambda_notify.function_arn
}

output "lambda_predict_arn" {
  description = "Predict Lambda function ARN"
  value       = module.lambda_predict.function_arn
}

# ── SNS ───────────────────────────────────────────────────────────────────

output "sns_topic_arn" {
  description = "Pipeline notifications SNS topic ARN"
  value       = module.sns_notify.topic_arn
}
