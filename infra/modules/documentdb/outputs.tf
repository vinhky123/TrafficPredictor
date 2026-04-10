output "endpoint" {
  value = aws_docdb_cluster.this.endpoint
}

output "connection_string" {
  value     = "mongodb://${var.master_username}:${var.master_password}@${aws_docdb_cluster.this.endpoint}:27017/?retryWrites=false"
  sensitive = true
}
