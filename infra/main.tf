locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# ── Networking ─────────────────────────────────────────────────────────────

module "networking" {
  source = "./modules/networking"

  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

# ── ECR ────────────────────────────────────────────────────────────────────

module "ecr" {
  source = "./modules/ecr"

  name_prefix = local.name_prefix
}

# ── S3 Buckets ─────────────────────────────────────────────────────────────

module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
}

# ── DynamoDB ───────────────────────────────────────────────────────────────

module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix = local.name_prefix
}

# ── Lambda Execution Role (common policy ARNs) ────────────────────────────

locals {
  basic_policy_arn   = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  vpc_policy_arn     = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# ── Lambda: REST API Handler ──────────────────────────────────────────────

module "lambda_api" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-api"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 30
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "api/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for DynamoDB read access on segments/speeds/predictions tables
    # TODO: attach policy for S3 read access on processed bucket
  ]

  environment_variables = {
    SEGMENTS_TABLE    = module.dynamodb.segments_table_name
    SPEEDS_TABLE      = module.dynamodb.speeds_table_name
    PREDICTIONS_TABLE = module.dynamodb.predictions_table_name
  }
}

# ── Lambda: Extract (HERE API → raw S3) ───────────────────────────────────

module "lambda_extract" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-extract"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 120
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "extract/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for S3 write access on raw bucket
  ]

  environment_variables = {
    RAW_BUCKET   = module.s3.raw_bucket_name
    HERE_API_KEY = var.here_api_key
  }
}

# ── Lambda: Transform (raw S3 → processed S3) ─────────────────────────────

module "lambda_transform" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-transform"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 512
  timeout       = 300
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "transform/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for S3 read/write access on raw and processed buckets
  ]

  environment_variables = {
    RAW_BUCKET      = module.s3.raw_bucket_name
    PROCESSED_BUCKET = module.s3.processed_bucket_name
  }
}

# ── Lambda: Load (processed S3 → DynamoDB) ────────────────────────────────

module "lambda_load" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-load"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 512
  timeout       = 300
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "load/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for S3 read access on processed bucket
    # TODO: attach policy for DynamoDB write access on speeds table
  ]

  environment_variables = {
    PROCESSED_BUCKET = module.s3.processed_bucket_name
    SPEEDS_TABLE     = module.dynamodb.speeds_table_name
  }
}

# ── Lambda: SSE Notify ────────────────────────────────────────────────────

module "lambda_notify" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-notify"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 30
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "notify/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for DynamoDB read access on connections table
    # TODO: attach policy for SNS publish on notification topic
  ]

  environment_variables = {
    CONNECTIONS_TABLE = module.dynamodb.connections_table_name
    SNS_TOPIC_ARN     = module.sns_notify.topic_arn
  }
}

# ── Lambda: WebSocket Connect ─────────────────────────────────────────────

module "lambda_connect" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-connect"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 128
  timeout       = 10
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "connect/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for DynamoDB write access on connections table
  ]

  environment_variables = {
    CONNECTIONS_TABLE = module.dynamodb.connections_table_name
  }
}

# ── Lambda: WebSocket Disconnect ──────────────────────────────────────────

module "lambda_disconnect" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-disconnect"
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 128
  timeout       = 10
  s3_bucket     = module.s3.lambdas_bucket_name
  s3_key        = "disconnect/function.zip"

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for DynamoDB write access on connections table
  ]

  environment_variables = {
    CONNECTIONS_TABLE = module.dynamodb.connections_table_name
  }
}

# ── Lambda: Predict (Container) ───────────────────────────────────────────

module "lambda_predict" {
  source = "./modules/lambda-function"

  function_name = "${local.name_prefix}-predict"
  package_type  = "Container"
  image_uri     = "${module.ecr.predict_repo_url}:latest"
  memory_size   = 1024
  timeout       = 120

  policies = [
    local.basic_policy_arn,
    # TODO: attach policy for DynamoDB read access on segments/speeds/predictions tables
    # TODO: attach policy for S3 read access on models bucket
  ]

  environment_variables = {
    SEGMENTS_TABLE    = module.dynamodb.segments_table_name
    SPEEDS_TABLE      = module.dynamodb.speeds_table_name
    PREDICTIONS_TABLE = module.dynamodb.predictions_table_name
    MODELS_BUCKET     = module.s3.models_bucket_name
  }
}

# ── API Gateway ───────────────────────────────────────────────────────────

module "api_gateway" {
  source = "./modules/api-gateway"

  api_name          = "${local.name_prefix}-api"
  lambda_arn        = module.lambda_api.function_arn
  lambda_invoke_arn = module.lambda_api.invoke_arn
}

# ── SSE API Gateway ───────────────────────────────────────────────────────

module "sse_api" {
  source = "./modules/sse-api-gateway"

  api_name          = "${local.name_prefix}-sse"
  lambda_arn        = module.lambda_notify.function_arn
  lambda_invoke_arn = module.lambda_notify.invoke_arn
}

# ── Step Function ─────────────────────────────────────────────────────────

resource "aws_iam_role" "step_function" {
  name = "${local.name_prefix}-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "step_function" {
  name = "${local.name_prefix}-step-function-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "lambda:InvokeFunction"
        Resource = [
          module.lambda_extract.function_arn,
          module.lambda_transform.function_arn,
          module.lambda_load.function_arn,
          module.lambda_notify.function_arn,
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "step_function" {
  role       = aws_iam_role.step_function.name
  policy_arn = aws_iam_policy.step_function.arn
}

locals {
  step_function_definition = jsonencode({
    Comment = "Traffic Data ETL Pipeline"
    StartAt = "Extract"
    States = {
      Extract = {
        Type     = "Task"
        Resource = module.lambda_extract.function_arn
        Next     = "Transform"
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2
          }
        ]
      }
      Transform = {
        Type     = "Task"
        Resource = module.lambda_transform.function_arn
        Next     = "Load"
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2
          }
        ]
      }
      Load = {
        Type     = "Task"
        Resource = module.lambda_load.function_arn
        Next     = "Notify"
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2
          }
        ]
      }
      Notify = {
        Type     = "Task"
        Resource = module.lambda_notify.function_arn
        End      = true
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2
          }
        ]
      }
    }
  })
}

module "step_function" {
  source = "./modules/step-function"

  name       = "${local.name_prefix}-etl-pipeline"
  definition = local.step_function_definition
  role_arn   = aws_iam_role.step_function.arn
  type       = "STANDARD"
}

# ── EventBridge Schedule ──────────────────────────────────────────────────

resource "aws_iam_role" "eventbridge" {
  name = "${local.name_prefix}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "eventbridge" {
  name = "${local.name_prefix}-eventbridge-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "states:StartExecution"
        Resource = module.step_function.state_machine_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eventbridge" {
  role       = aws_iam_role.eventbridge.name
  policy_arn = aws_iam_policy.eventbridge.arn
}

module "etl_schedule" {
  source = "./modules/eventbridge"

  name                = "${local.name_prefix}-etl-schedule"
  schedule_expression = "rate(5 minutes)"
  target_arn          = module.step_function.state_machine_arn
  target_role_arn     = aws_iam_role.eventbridge.arn
}

# ── SNS Topic ─────────────────────────────────────────────────────────────

module "sns_notify" {
  source = "./modules/sns"

  name = "${local.name_prefix}-pipeline-notifications"
}
