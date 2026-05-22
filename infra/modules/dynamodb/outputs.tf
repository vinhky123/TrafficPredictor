output "segments_table_name" {
  value = aws_dynamodb_table.segments.name
}

output "segments_table_arn" {
  value = aws_dynamodb_table.segments.arn
}

output "segments_gsi_arn" {
  value = "${aws_dynamodb_table.segments.arn}/index/SegmentIndexGSI"
}

output "speeds_table_name" {
  value = aws_dynamodb_table.speeds.name
}

output "speeds_table_arn" {
  value = aws_dynamodb_table.speeds.arn
}

output "predictions_table_name" {
  value = aws_dynamodb_table.predictions.name
}

output "predictions_table_arn" {
  value = aws_dynamodb_table.predictions.arn
}

output "connections_table_name" {
  value = aws_dynamodb_table.connections.name
}

output "connections_table_arn" {
  value = aws_dynamodb_table.connections.arn
}
