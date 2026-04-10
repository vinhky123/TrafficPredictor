output "webserver_url" {
  value = aws_mwaa_environment.this.webserver_url
}

output "environment_arn" {
  value = aws_mwaa_environment.this.arn
}
