output "data_bucket_name" {
  value = aws_s3_bucket.data.id
}

output "data_bucket_arn" {
  value = aws_s3_bucket.data.arn
}

output "raw_bucket_name" {
  value = aws_s3_bucket.raw.id
}

output "raw_bucket_arn" {
  value = aws_s3_bucket.raw.arn
}

output "processed_bucket_name" {
  value = aws_s3_bucket.processed.id
}

output "processed_bucket_arn" {
  value = aws_s3_bucket.processed.arn
}

output "lambdas_bucket_name" {
  value = aws_s3_bucket.lambdas.id
}

output "lambdas_bucket_arn" {
  value = aws_s3_bucket.lambdas.arn
}

output "models_bucket_name" {
  value = aws_s3_bucket.models.id
}

output "models_bucket_arn" {
  value = aws_s3_bucket.models.arn
}
