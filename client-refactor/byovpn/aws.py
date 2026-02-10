from util import generate_server_config, get_public_ip

from typing import Tuple
import pulumi
from pulumi import automation
import pulumi_aws as aws


def get_or_create_secgrp(server_port: int = 33333, allowed_ips: str = None) -> aws.ec2.SecurityGroup:
    """Get or create a security group that allows UDP traffic on the WireGuard server port."""
    sg_name = "wg_secgrp"
    sg_tags = {
        "Name": "byob_wg_secgrp",
        "managed_by": "pulumi"
    }
    
    existing_sg = aws.ec2.security_group.get(
        name=sg_name,
        tags=sg_tags
    )

    if existing_sg:
        return existing_sg
    else:
        new_sg = aws.ec2.SecurityGroup(
            sg_name,
            description="Security group for WireGuard BYOVPN server",
            tags=sg_tags,
            ingress=[{
                "from_port": 0,
                "to_port": server_port,
                "protocol": "udp",
                "cidr_blocks": [allowed_ips if allowed_ips else "0.0.0.0/0"]
                "description": "Allow WireGuard VPN traffic"
            }]
        )
        return new_sg


def launch_byovpn_ec2(server_port: int,
               server_private_key: str,
               client_public_key: str,
               fetch_client_ip: bool = False) -> Tuple[str, str]:
    ubuntu = aws.ec2.get_ami(most_recent=True,
        filters=[
            {
                "name": "name",
                "values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
            },
            {
                "name": "virtualization-type",
                "values": ["hvm"],
            },
        ],
        owners=["099720109477"])
    
    if fetch_client_ip:
        client_ip = get_public_ip()
        allowed_ips = f"{client_ip}/32"
    
    group = get_or_create_secgrp(allowed_ips=allowed_ips)

    server_config = generate_server_config(server_port, server_private_key, client_public_key)
