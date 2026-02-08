provider "aws" {
  region = "us-east-1"
}

resource "wireguard_asymmetric_key" "client_key" {
}

resource "wireguard_asymmetric_key" "server_key" {
}

data "http" "myip" {
  url = "https://ipv4.icanhazip.com"
}

locals {
  wg0_config = templatefile("${path.module}/wg-conf/client.conf.tpfpl", {
    server_private_key = wireguard_asymmetric_key.server_key.private_key
    client_private_key = wireguard_asymmetric_key.client_key.private_key
    allowed_ips        = data.http.myip.body
  })

  client_config = templatefile("${path.module}/client.conf.tpfpl", {
    server_public_key  = wireguard_asymmetric_key.server_key.public_key
    server_public_ip   = data.http.myip.body
    server_listen_port = variable.server_port
    allowed_ips        = data.http.myip.body
  })

}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical

}

resource "aws_instance" "vpn_server" {
  ami = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  tags = {
    Name = "VPN-Server"
  }
}

