resource "aws_dynamodb_table" "segments" {
  name         = "${var.name_prefix}-segments"
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
    Name = "${var.name_prefix}-segments"
  }
}

resource "aws_dynamodb_table" "speeds" {
  name         = "${var.name_prefix}-speeds"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "segment_index"
  range_key    = "timestamp"

  attribute {
    name = "segment_index"
    type = "N"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name = "${var.name_prefix}-speeds"
  }
}

resource "aws_dynamodb_table" "predictions" {
  name         = "${var.name_prefix}-predictions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "segment_index"
  range_key    = "timestamp"

  attribute {
    name = "segment_index"
    type = "N"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name = "${var.name_prefix}-predictions"
  }
}

resource "aws_dynamodb_table" "connections" {
  name         = "${var.name_prefix}-connections"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "connection_id"

  attribute {
    name = "connection_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.name_prefix}-connections"
  }
}
