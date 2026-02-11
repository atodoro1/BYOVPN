from util import generate_server_config, get_public_ip

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import pulumi
import pulumi_aws as aws


def check_aws_login():
    """
    Verifies that the user has valid AWS credentials configured.
    """
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        return True
    
    except (NoCredentialsError, ClientError):
        # NoCredentialsError: No keys found at all.
        # ClientError: Keys found, but invalid/expired.
        return False

def get_or_create_secgrp(server_port: int, allowed_ips: str = None) -> aws.ec2.SecurityGroup:
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
                "from_port": server_port,
                "to_port": server_port,
                "protocol": "udp",
                "cidr_blocks": [allowed_ips if allowed_ips else "0.0.0.0/0"],
                "description": "Allow WireGuard VPN traffic"
            }]
        )
        return new_sg


def launch_byovpn_ec2(server_port: int,
               server_private_key: str,
               client_public_key: str,
               fetch_client_ip: bool = False) -> None:
    """Launches an EC2 instance with WireGuard installed and configured, exporting the EC2's IP."""
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

    secgrp = get_or_create_secgrp(server_port, allowed_ips=allowed_ips)
    
    server_config = generate_server_config(server_port, server_private_key, client_public_key)

    # Adding the user data script to install WireGuard on the EC2 instance
    user_data_script = f"""
        #!/usr/bin/env bash
        
        apt-get update
        apt install -y  wireguard wireguard-tools openresolv

        cat << EOF > /etc/wireguard/wg0.conf
        {server_config}
        EOF

        IFACE="$(ip route show default | awk '{{print $5; exit}}')"
        sed -i "s/IFACE/${{IFACE}}/g" /etc/wireguard/wg0.conf

        chmod 600 /etc/wireguard/wg0.conf

        systemctl enable wg-quick@wg0
        systemctl start wg-quick@wg0
        """
    
    instance = aws.ec2.Instance(resource_name='byovpn_server',
                                instance_type='t3.micro',
                                ami=ubuntu.id,
                                tags={'Name': 'BYOVPN_Server'},
                                vpc_security_group_ids=[secgrp.id],
                                user_data=user_data_script)

    pulumi.export("public_ip", instance.public_ip)