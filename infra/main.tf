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

# ── DocumentDB ─────────────────────────────────────────────────────────────

module "documentdb" {
  source = "./modules/documentdb"

  name_prefix       = local.name_prefix
  subnet_ids        = module.networking.private_subnet_ids
  vpc_id            = module.networking.vpc_id
  allowed_sg_ids    = [module.ecs.backend_sg_id]
  instance_class    = var.docdb_instance_class
  master_username   = var.docdb_master_username
  master_password   = var.docdb_master_password
}

# ── DynamoDB (Road Segment Registry) ───────────────────────────────────────

module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix = local.name_prefix
}

# ── ECS (Backend) ──────────────────────────────────────────────────────────

module "ecs" {
  source = "./modules/ecs"

  name_prefix      = local.name_prefix
  vpc_id           = module.networking.vpc_id
  public_subnets   = module.networking.public_subnet_ids
  private_subnets  = module.networking.private_subnet_ids
  ecr_repo_url     = module.ecr.backend_repo_url
  cpu              = var.backend_cpu
  memory           = var.backend_memory
  desired_count    = var.backend_desired_count
  mongodb_uri      = module.documentdb.connection_string
  dynamodb_table   = module.dynamodb.table_name
  dynamodb_arn     = module.dynamodb.table_arn
  dynamodb_gsi_arn = module.dynamodb.gsi_arn
}

# ── MWAA (Managed Airflow) ─────────────────────────────────────────────────

module "mwaa" {
  source = "./modules/mwaa"

  name_prefix       = local.name_prefix
  vpc_id            = module.networking.vpc_id
  private_subnets   = module.networking.private_subnet_ids
  dag_s3_bucket     = module.s3.dag_bucket_name
  environment_class = var.mwaa_environment_class
  dynamodb_arn      = module.dynamodb.table_arn
  dynamodb_gsi_arn  = module.dynamodb.gsi_arn
}
