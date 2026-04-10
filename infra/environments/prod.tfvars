environment        = "prod"
aws_region         = "ap-southeast-1"
project_name       = "traffic-predictor"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1c"]

backend_cpu           = 1024
backend_memory        = 2048
backend_desired_count = 2

docdb_instance_class  = "db.r5.large"
docdb_master_username = "trafficadmin"

mwaa_environment_class = "mw1.medium"
