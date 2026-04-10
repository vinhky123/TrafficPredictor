output "cluster_id" {
  value = aws_ecs_cluster.this.id
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "backend_sg_id" {
  value = aws_security_group.backend.id
}
