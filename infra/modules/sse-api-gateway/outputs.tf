output "sse_url" {
  value = "${aws_api_gateway_stage.this.invoke_url}connect"
}

output "api_id" {
  value = aws_api_gateway_rest_api.this.id
}
