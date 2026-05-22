data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "this" {
  count      = length(var.policies)
  role       = aws_iam_role.this.name
  policy_arn = var.policies[count.index]
}

resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.this.arn
  package_type  = var.package_type
  memory_size   = var.memory_size
  timeout       = var.timeout

  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [true] : []
    content {
      variables = var.environment_variables
    }
  }

  dynamic "image_config" {
    for_each = var.package_type == "Container" && var.image_uri != null ? [true] : []
    content {
      # command and entrypoint can be added if needed
    }
  }

  image_uri = var.package_type == "Container" ? var.image_uri : null
  handler   = var.package_type == "Zip" ? var.handler : null
  runtime   = var.package_type == "Zip" ? var.runtime : null
  filename  = var.package_type == "Zip" ? var.filename : null
  source_code_hash = var.package_type == "Zip" && var.filename != null ? filebase64sha256(var.filename) : null
}
