resource "aws_dynamodb_table" "road_segments" {
  name         = "${var.name_prefix}-road-segments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "shape_hash"

  attribute {
    name = "shape_hash"
    type = "S"
  }

  attribute {
    name = "segment_index"
    type = "N"
  }

  global_secondary_index {
    name            = "SegmentIndexGSI"
    hash_key        = "segment_index"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.name_prefix}-road-segments"
  }
}
