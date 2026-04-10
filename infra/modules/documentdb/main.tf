resource "aws_security_group" "docdb" {
  name   = "${var.name_prefix}-docdb-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = var.allowed_sg_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_docdb_subnet_group" "this" {
  name       = "${var.name_prefix}-docdb-subnets"
  subnet_ids = var.subnet_ids
}

resource "aws_docdb_cluster_parameter_group" "this" {
  family = "docdb5.0"
  name   = "${var.name_prefix}-params"

  parameter {
    name  = "tls"
    value = "disabled"
  }
}

resource "aws_docdb_cluster" "this" {
  cluster_identifier              = "${var.name_prefix}-docdb"
  engine                          = "docdb"
  master_username                 = var.master_username
  master_password                 = var.master_password
  db_subnet_group_name            = aws_docdb_subnet_group.this.name
  db_cluster_parameter_group_name = aws_docdb_cluster_parameter_group.this.name
  vpc_security_group_ids          = [aws_security_group.docdb.id]
  skip_final_snapshot             = true
  deletion_protection             = false
}

resource "aws_docdb_cluster_instance" "this" {
  count              = 1
  identifier         = "${var.name_prefix}-docdb-0"
  cluster_identifier = aws_docdb_cluster.this.id
  instance_class     = var.instance_class
}
