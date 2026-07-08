terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    http = {
      source = "hashicorp/http"
    }
  }
}

data "http" "my_public_ip" {
  url = "https://checkip.amazonaws.com/"
}

locals {
  my_ip_cidr = "${chomp(data.http.my_public_ip.response_body)}/32"
}

provider "aws" {
  region  = "ap-northeast-2"
  profile = "Terra-user"
}

resource "aws_vpc" "terra_vpc" {
  cidr_block           = "192.168.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "terra_vpc"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.terra_vpc.id

  tags = {
    Name = "main"
  }
}

resource "aws_subnet" "terra_open_subnet" {
  vpc_id                  = aws_vpc.terra_vpc.id
  cidr_block              = "192.168.1.0/24"
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "terra_open_subnet"
  }
}

resource "aws_subnet" "terra_close_subnet" {
  vpc_id                  = aws_vpc.terra_vpc.id
  cidr_block              = "192.168.10.0/24"
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = false
  tags = {
    Name = "terra_close_subnet"
  }
}


resource "aws_security_group" "open_sg" {
  name   = "open_sg"
  vpc_id = aws_vpc.terra_vpc.id

  ingress {
    description = "Allow HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [local.my_ip_cidr]
  }

  ingress {
    description = "Allow all ICMP from current public IP"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = [local.my_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "close_sg" {
  name   = "close_sg"
  vpc_id = aws_vpc.terra_vpc.id

  ingress {
    description     = "Allow DB from open_sg"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.open_sg.id]
  }

  ingress {
    description     = "Allow SSH from open_sg"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.open_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "close_sg"
  }
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.terra_vpc.id
  service_name      = "com.amazonaws.ap-northeast-2.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.terra_close_rt.id
  ]

  tags = {
    Name = "s3-endpoint-for-db"
  }
}

locals {
  common_user_data = file("${path.module}/user_data/00-common.sh")
  db_user_data     = file("${path.module}/user_data/10-db-install.sh")
  web_user_data    = file("${path.module}/user_data/20-web-install.sh")
}

resource "aws_instance" "terra_DB" {
  ami                    = "ami-0b1cb107a74bad43e"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.terra_close_subnet.id
  key_name               = "asd-close"
  vpc_security_group_ids = [aws_security_group.close_sg.id]
  private_ip             = "192.168.10.13"

  depends_on = [
    aws_route_table_association.terra_close_assoc,
    aws_vpc_endpoint.s3
  ]

  user_data = join("\n", [
    local.common_user_data,
    local.db_user_data
  ])

  tags = {
    Name = "terra_DB"
  }
}

resource "aws_route_table" "terra_close_rt" {
  vpc_id = aws_vpc.terra_vpc.id
  tags = {
    Name = "terra_close_rt"
  }
}
resource "aws_route_table_association" "terra_close_assoc" {
  subnet_id      = aws_subnet.terra_close_subnet.id
  route_table_id = aws_route_table.terra_close_rt.id
}





resource "aws_instance" "terra_WEB" {
  ami                         = "ami-0b1cb107a74bad43e"
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.terra_open_subnet.id
  key_name                    = "asd-open"
  vpc_security_group_ids      = [aws_security_group.open_sg.id]
  associate_public_ip_address = true
  private_ip                  = "192.168.1.13"

  user_data = join("\n", [
    local.common_user_data,
    local.web_user_data
  ])

  tags = {
    Name = "terra_WEB"
  }
}

resource "aws_route_table" "terra_open_rt" {
  vpc_id = aws_vpc.terra_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "terra_open_rt"
  }
}
resource "aws_route_table_association" "terra_open_assoc" {
  subnet_id      = aws_subnet.terra_open_subnet.id
  route_table_id = aws_route_table.terra_open_rt.id
}