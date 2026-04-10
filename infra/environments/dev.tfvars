environment        = "dev"
aws_region         = "ap-southeast-1"
project_name       = "traffic-predictor"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]

backend_cpu           = 512
backend_memory        = 1024
backend_desired_count = 1

docdb_instance_class  = "db.t3.medium"
docdb_master_username = "trafficadmin"

mwaa_environment_class = "mw1.small"
