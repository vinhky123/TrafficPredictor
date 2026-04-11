output "table_name" {
  value = aws_dynamodb_table.road_segments.name
}

output "table_arn" {
  value = aws_dynamodb_table.road_segments.arn
}

output "gsi_arn" {
  value = "${aws_dynamodb_table.road_segments.arn}/index/SegmentIndexGSI"
}
