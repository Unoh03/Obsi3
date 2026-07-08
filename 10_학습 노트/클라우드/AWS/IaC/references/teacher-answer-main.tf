terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
provider "aws" {
  profile = "terra-user"
}
resource "aws_vpc" "quiz-vpc" {
  cidr_block           = "192.168.0.0/16"
  tags                 = { Name = "quiz-vpc" }
  enable_dns_hostnames = true
  enable_dns_support   = true
}
resource "aws_subnet" "quiz-public-subnet-2a" {
  vpc_id                  = aws_vpc.quiz-vpc.id
  cidr_block              = "192.168.10.0/24"
  tags                    = { Name = "quiz-public-subnet-2a" }
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = true
}
resource "aws_subnet" "quiz-public-subnet-2c" {
  vpc_id                  = aws_vpc.quiz-vpc.id
  cidr_block              = "192.168.30.0/24"
  tags                    = { Name = "quiz-public-subnet-2c" }
  availability_zone       = "ap-northeast-2c"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "quiz-private-subnet-2a" {
  vpc_id            = aws_vpc.quiz-vpc.id
  cidr_block        = "192.168.11.0/24"
  tags              = { Name = "quiz-private-subnet-2a" }
  availability_zone = "ap-northeast-2a"

}
resource "aws_subnet" "quiz-private-subnet-2c" {
  vpc_id            = aws_vpc.quiz-vpc.id
  cidr_block        = "192.168.31.0/24"
  tags              = { Name = "quiz-private-subnet-2c" }
  availability_zone = "ap-northeast-2c"
}

resource "aws_internet_gateway" "quiz-igw" {
  vpc_id = aws_vpc.quiz-vpc.id
  tags   = { Name = "quiz-igw" }
}

resource "aws_route_table" "quiz-public-rt" {
  vpc_id = aws_vpc.quiz-vpc.id
  route {
    gateway_id = aws_internet_gateway.quiz-igw.id
    cidr_block = "0.0.0.0/0"
  }
  tags = { Name = "quiz-public-rt" }
}

resource "aws_route_table_association" "quiz-public-rt-2a" {
  route_table_id = aws_route_table.quiz-public-rt.id
  subnet_id      = aws_subnet.quiz-public-subnet-2a.id
}
resource "aws_route_table_association" "quiz-public-rt-2c" {
  route_table_id = aws_route_table.quiz-public-rt.id
  subnet_id      = aws_subnet.quiz-public-subnet-2c.id
}

resource "aws_route_table" "quiz-private-rt" {
  vpc_id = aws_vpc.quiz-vpc.id
  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = aws_instance.quiz-nat-instance.primary_network_interface_id
  }
   tags = { Name = "quiz-private-rt" }
}
resource "aws_route_table_association" "quiz-private-rt-2a" {
  route_table_id = aws_route_table.quiz-private-rt.id
  subnet_id      = aws_subnet.quiz-private-subnet-2a.id
}
resource "aws_route_table_association" "quiz-private-rt-2c" {
  route_table_id = aws_route_table.quiz-private-rt.id
  subnet_id      = aws_subnet.quiz-private-subnet-2c.id
}
resource "aws_instance" "quiz-bastion-instance" {
  ami                    = "ami-0bc151a94289adb52"
  instance_type          = "t3.micro"
  key_name               = "my-public-ec2-key"
  subnet_id              = aws_subnet.quiz-public-subnet-2c.id
  vpc_security_group_ids = [aws_security_group.quiz-bastion-sg.id]
  tags = {
    Name = "quiz-bastion-instance"
  }
}
resource "aws_instance" "quiz-nat-instance" {
  ami                    = "ami-0bc151a94289adb52"
  instance_type          = "t3.micro"
  key_name               = "my-public-ec2-key"
  subnet_id              = aws_subnet.quiz-public-subnet-2a.id
  vpc_security_group_ids = [aws_security_group.quiz-nat-sg.id]
  tags = {
    Name = "quiz-nat-instance"
  }
  source_dest_check = false
}
resource "aws_instance" "quiz-private-instance" {
  ami                    = "ami-0bc151a94289adb52"
  instance_type          = "t3.micro"
  key_name               = "my-private-ec2-key"
  subnet_id              = aws_subnet.quiz-private-subnet-2a.id
  vpc_security_group_ids = [aws_security_group.quiz-private-sg.id]
  tags = {
    Name = "quiz-private-instance"
  }
}
resource "aws_security_group" "quiz-bastion-sg" {
  vpc_id      = aws_vpc.quiz-vpc.id
  name_prefix = -1
  description = "bastion host security group"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "quiz-nat-sg" {
  vpc_id      = aws_vpc.quiz-vpc.id
  name_prefix = -1
  description = "NAT instance security group"
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "quiz-private-sg" {
  vpc_id      = aws_vpc.quiz-vpc.id
  name_prefix = -1
  description = "private ec2 security group"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "ICMP"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}