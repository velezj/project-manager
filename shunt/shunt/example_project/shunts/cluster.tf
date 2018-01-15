{% import 'variables' as variables %}

###
###
### Useful Commands
###
### use bastion host:
### ssh -i financial-models-demo-devops-key -o ProxyCommand="ssh -i financial-models-demo-devops-key -W %h:%p ubuntu@<EIP=18.218.67.87>" ubuntu@<TARGET=10.0.0.2X>

provider "aws" {
  profile = "{{ variables.aws_profile }}"
  region = "{{ variables.aws_region }}"
}

variable "salt_minion_ips" {
  default = {
    "0" = "10.0.0.20"
    "1" = "10.0.0.21"
    "2" = "10.0.0.22"
    "3" = "10.0.0.23"
    "4" = "10.0.0.24"
    "5" = "10.0.0.25"
    "6" = "10.0.0.26"
    "7" = "10.0.0.27"
  }
}


####
# VPC
####

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/24"
  enable_dns_hostnames = true
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 vpc main"    
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = "${aws_vpc.main.id}"
}

resource "aws_security_group" "allow_all_inbound_and_vpc" {
  name        = "allow_all_inbound_and_vpc"
  description = "Allow all inbound traffic, vpc can talk to itself"
  vpc_id      = "${aws_vpc.main.id}"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks     = ["10.0.0.0/24"]
  }

  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 security-group allow-all-inbound allow-vpc-outbound"
  }

}

resource "aws_security_group" "vpc_only" {
  name        = "vpc_only"
  description = "VPC inbound nad outbound only"
  vpc_id      = "${aws_vpc.main.id}"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/24"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks     = ["10.0.0.0/24"]
  }

  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 security-group vpc-only"
  }

}

resource "aws_security_group" "vpc_in_all_out" {
  name        = "vpc_in_all_out"
  description = "VPC inbound and all outbound"
  vpc_id      = "${aws_vpc.main.id}"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/24"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks     = ["0.0.0.0/0"]
  }

  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 security-group vpc-in all-out"
  }

}


resource "aws_security_group" "bastion" {
  name        = "bastion"
  description = "VPC Bastion"
  vpc_id      = "${aws_vpc.main.id}"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks     = ["0.0.0.0/0"]
  }

  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 security-group bastion"
  }

}

resource "aws_subnet" "public" {
  vpc_id = "${aws_vpc.main.id}"
  cidr_block = "10.0.0.128/25"
  availability_zone = "{{ variables.aws_region }}a"

  map_public_ip_on_launch = false

  depends_on = ["aws_internet_gateway.main"]
  
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 subnet public"
  }
}

resource "aws_eip" "nat" {
  vpc = true

  associate_with_private_ip = "10.0.0.101"
  depends_on                = ["aws_internet_gateway.main"]
}

resource "aws_subnet" "private" {
  vpc_id = "${aws_vpc.main.id}"
  cidr_block = "10.0.0.0/25"
  availability_zone = "{{ variables.aws_region }}a"

  map_public_ip_on_launch = false

  depends_on = ["aws_internet_gateway.main"]
  
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 subnet private"
  }
}


resource "aws_nat_gateway" "nat" {
  allocation_id = "${aws_eip.nat.id}"
  subnet_id = "${aws_subnet.public.id}"
  depends_on = ["aws_internet_gateway.main"]
}

resource "aws_route_table" "nat-private-to-outside" {
  vpc_id = "${aws_vpc.main.id}"
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_nat_gateway.nat.id}"
  }
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 route-table nat-private-to-outside"
  }
}

resource "aws_route_table_association" "nat" {
  subnet_id = "${aws_subnet.private.id}"
  route_table_id = "${aws_route_table.nat-private-to-outside.id}"
}

####
# SSH KEYS
####

resource "aws_key_pair" "devops" {
  key_name = "devops-key"
  public_key = "${file("{{ variables.devops_key }}.pub")}"
}


####
# CLUSTER in VPC
####

resource "aws_network_interface" "net" {
  subnet_id = "${aws_subnet.private.id}"
  private_ips = ["10.0.0.10"]
  security_groups = ["${aws_security_group.vpc_in_all_out.id}"]
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 network-interface vpc"
  }
}


data "aws_ami" "salt_master" {
  most_recent = true

  filter {
    name = "name"
    values = [ "*{{ variables.project }}*salt-master*" ]
  }
  owners = ["self"]
}

resource "aws_instance" "master" {
  count = "1"
  ami = "${data.aws_ami.salt_master.id}"
  instance_type = "{{ variables.salt_master_instance_type }}"
  key_name = "${aws_key_pair.devops.key_name}"

  network_interface {
    network_interface_id = "${aws_network_interface.net.id}"
    device_index = 0
  }

  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Salt = "master"
    Name = "{{ variables.project }} dev-cluster-01 ec2-instance salt-master master"
  }
  
}


data "aws_ami" "salt_minion" {
  most_recent = true

  filter {
    name = "name"
    values = [ "*{{variables.project}}*salt-minion*" ]
  }
  owners = ["self"]
}

resource "aws_instance" "minion" {
  count = "{{ variables.number_of_minions }}"
  ami = "${data.aws_ami.salt_minion.id}"
  instance_type = "{{ variables.salt_minion_instance_type }}"
  key_name = "${aws_key_pair.devops.key_name}"

  vpc_security_group_ids = ["${aws_security_group.vpc_in_all_out.id}"]
  subnet_id = "${aws_subnet.private.id}"
  private_ip = "${lookup(var.salt_minion_ips, count.index)}"
  
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Salt = "minion"
    Name = "{{ variables.project }} dev-cluster-01 ec2-instance salt-master minion"
  }
  
}

####
# BASTION
####

resource "aws_network_interface" "bastion-net" {
  subnet_id = "${aws_subnet.public.id}"
  private_ips = ["10.0.0.200"]
  security_groups = ["${aws_security_group.bastion.id}"]
  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 network-interface bastion"
  }
}

data "aws_route_table" "bastion" {
  vpc_id = "${aws_vpc.main.id}"
  filter {
    name = "association.main"
    values = [ "true" ]
  }
}

# make sure to actually *use* our internet gateway for the bastion hosts
resource "aws_route" "bastion" {
  route_table_id = "${data.aws_route_table.bastion.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id = "${aws_internet_gateway.main.id}"
}


data "aws_ami" "bastion" {
  most_recent = true

  filter {
    name = "name"
    values = [ "*{{ variables.project }}*bastion*" ]
  }
  owners = ["self"]
}

resource "aws_instance" "bastion" {
  count = "1"
  ami = "${data.aws_ami.bastion.id}"
  instance_type = "{{variables.bastion_instance_type}}"
  key_name = "${aws_key_pair.devops.key_name}"

  network_interface {
    network_interface_id = "${aws_network_interface.bastion-net.id}"
    device_index = 0
  }

  tags {
    Project = "{{ variables.project }}"
    Role = "dev"
    Automated = "true"
    Terraform = "true"
    Name = "{{ variables.project }} dev-cluster-01 ec2-instance bastion"
  }
  
}

resource "aws_eip" "bastion" {
  vpc = true

  instance                  = "${aws_instance.bastion.id}"
  associate_with_private_ip = "10.0.0.200"
  depends_on                = ["aws_internet_gateway.main"]
}


####
# OUTPUTS
####

output "bastion-ip" {
  value = "${aws_eip.bastion.public_ip}"
}

output "nat-ip" {
  value = "${aws_eip.nat.public_ip}"
}
