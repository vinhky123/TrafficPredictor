output "backend_repo_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "airflow_repo_url" {
  value = aws_ecr_repository.airflow.repository_url
}
