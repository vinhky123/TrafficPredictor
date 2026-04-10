# Infrastructure — Terraform

Modular Terraform configuration that deploys the full TrafficPredictor stack on AWS (everything except the frontend, which is deployed on Vercel).

## Architecture Provisioned

| Module | AWS Service | Purpose |
|--------|-------------|---------|
| `networking` | VPC, Subnets, NAT Gateway | Network isolation with public/private subnets |
| `ecr` | Elastic Container Registry | Docker image repositories for backend & Airflow |
| `ecs` | ECS Fargate + ALB | Runs the Flask backend as a serverless container |
| `mwaa` | Managed Workflows for Apache Airflow | Managed Airflow environment for ETL orchestration |
| `documentdb` | Amazon DocumentDB | MongoDB-compatible database for traffic data |
| `s3` | S3 | Raw/transformed data storage + Airflow DAG bucket |

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.5
- AWS CLI configured with appropriate credentials
- An S3 bucket + DynamoDB table for Terraform remote state (see `providers.tf`)

## Usage

```bash
cd infra

# Initialize
terraform init

# Plan (dev)
terraform plan -var-file=environments/dev.tfvars -var="docdb_master_password=YOUR_PASSWORD"

# Apply
terraform apply -var-file=environments/dev.tfvars -var="docdb_master_password=YOUR_PASSWORD"

# Destroy
terraform destroy -var-file=environments/dev.tfvars -var="docdb_master_password=YOUR_PASSWORD"
```

## Module Structure

```
infra/
├── main.tf              # Root module — wires all modules together
├── variables.tf         # Input variables
├── outputs.tf           # Stack outputs (ALB DNS, endpoints, etc.)
├── providers.tf         # AWS provider + S3 backend config
├── environments/
│   ├── dev.tfvars       # Dev environment values
│   └── prod.tfvars      # Production environment values
└── modules/
    ├── networking/      # VPC, subnets, NAT, route tables
    ├── ecr/             # Container registries
    ├── ecs/             # Fargate cluster, task, service, ALB
    ├── mwaa/            # Managed Airflow environment
    ├── documentdb/      # DocumentDB cluster + instance
    └── s3/              # Data + DAG S3 buckets
```

## Deploying Application Code

After infrastructure is provisioned:

```bash
# Build and push backend image
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -t traffic-predictor-backend ./backend
docker tag traffic-predictor-backend:latest <backend_ecr_repo>:latest
docker push <backend_ecr_repo>:latest

# Upload DAGs to MWAA S3 bucket
aws s3 sync ./airflow/dags/ s3://<dag_bucket>/dags/

# Force new ECS deployment
aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment
```
