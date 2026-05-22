output "backend_repo_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "airflow_repo_url" {
  value = aws_ecr_repository.airflow.repository_url
}

output "predict_repo_url" {
  value = aws_ecr_repository.predict.repository_url
}
