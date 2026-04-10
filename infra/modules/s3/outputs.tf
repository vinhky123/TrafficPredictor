output "data_bucket_name" {
  value = aws_s3_bucket.data.id
}

output "data_bucket_arn" {
  value = aws_s3_bucket.data.arn
}

output "dag_bucket_name" {
  value = aws_s3_bucket.dags.id
}

output "dag_bucket_arn" {
  value = aws_s3_bucket.dags.arn
}
