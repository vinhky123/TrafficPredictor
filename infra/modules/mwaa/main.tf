# ── IAM ────────────────────────────────────────────────────────────────────

data "aws_iam_policy_document" "mwaa_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["airflow.amazonaws.com", "airflow-env.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "mwaa" {
  name               = "${var.name_prefix}-mwaa-role"
  assume_role_policy = data.aws_iam_policy_document.mwaa_assume.json
}

data "aws_iam_policy_document" "mwaa_policy" {
  statement {
    actions = [
      "s3:GetObject*",
      "s3:PutObject*",
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      "arn:aws:s3:::${var.dag_s3_bucket}",
      "arn:aws:s3:::${var.dag_s3_bucket}/*",
    ]
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:GetLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:log-group:airflow-*"]
  }

  statement {
    actions = [
      "sqs:*",
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:GenerateDataKey*",
      "kms:Encrypt",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "mwaa" {
  name   = "${var.name_prefix}-mwaa-policy"
  role   = aws_iam_role.mwaa.id
  policy = data.aws_iam_policy_document.mwaa_policy.json
}

# ── Security group ─────────────────────────────────────────────────────────

resource "aws_security_group" "mwaa" {
  name   = "${var.name_prefix}-mwaa-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── MWAA environment ──────────────────────────────────────────────────────

resource "aws_mwaa_environment" "this" {
  name               = "${var.name_prefix}-airflow"
  airflow_version    = "2.10.3"
  environment_class  = var.environment_class
  execution_role_arn = aws_iam_role.mwaa.arn

  source_bucket_arn = "arn:aws:s3:::${var.dag_s3_bucket}"
  dag_s3_path       = "dags/"

  network_configuration {
    security_group_ids = [aws_security_group.mwaa.id]
    subnet_ids         = slice(var.private_subnets, 0, 2)
  }

  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = "INFO"
    }
    scheduler_logs {
      enabled   = true
      log_level = "INFO"
    }
    webserver_logs {
      enabled   = true
      log_level = "INFO"
    }
    worker_logs {
      enabled   = true
      log_level = "INFO"
    }
    task_logs {
      enabled   = true
      log_level = "INFO"
    }
  }

  webserver_access_mode = "PUBLIC_ONLY"

  max_workers = 2
  min_workers = 1
}
