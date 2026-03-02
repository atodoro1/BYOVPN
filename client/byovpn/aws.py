from util import generate_server_config

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import pulumi
import pulumi_aws as aws
import subprocess


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

def get_or_create_secgrp(server_port: int, allowed_ips: str) -> aws.ec2.SecurityGroup:
    """Get or create a security group that allows UDP traffic on the WireGuard server port."""
    sg_name = "wg_secgrp"
    sg_tags = {
        "Name": "byob_wg_secgrp",
        "managed_by": "pulumi"
    }

    new_sg = aws.ec2.SecurityGroup(
        sg_name,
        description="Security group for WireGuard BYOVPN server",
        tags=sg_tags,
        ingress=[{
            "from_port": server_port,
            "to_port": server_port,
            "protocol": "udp",
            "cidr_blocks": [allowed_ips],
            "description": "Allow WireGuard VPN traffic"
        }
        ],
        egress=[{
            "from_port": 0,
            "to_port": 0,
            "protocol": "-1",
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound traffic"
        }]
    )
    return new_sg


def launch_byovpn_ec2(server_port: int,
               server_private_key: str,
               client_public_key: str,
               allowed_ips: str) -> None:
    """Launches an EC2 instance with WireGuard installed and configured, exporting the EC2's IP."""
    debian = aws.ec2.get_ami(most_recent=True,
        filters=[
            {
                "name": "name",
                "values": ["debian-12-amd64-*"],
            },
            {
                "name": "virtualization-type",
                "values": ["hvm"],
            },
        ],
        owners=["136693071363"]) # Debain Project's AWS account ID

    secgrp = get_or_create_secgrp(server_port, allowed_ips)
    
    server_config = generate_server_config(server_port, server_private_key, client_public_key)

    # Adding the user data script to install WireGuard on the EC2 instance
    user_data_script = f"""#!/usr/bin/env bash
echo "admin:thisisthepassword" | chpasswd
usermod -U admin
apt-get update
apt install -y wireguard wireguard-tools openresolv
sysctl -w net.ipv4.ip_forward=1
cat << EOF > /etc/wireguard/wg0.conf
{server_config}
EOF
IFACE="$(ip route show default | awk '{{print $5; exit}}')"
sed -i "s/IFACE/${{IFACE}}/g" /etc/wireguard/wg0.conf
chmod 600 /etc/wireguard/wg0.conf
wg-quick up wg0
"""
    
    instance = aws.ec2.Instance(resource_name='byovpn_server',
                                instance_type='t3.micro',
                                ami=debian.id,
                                tags={'Name': 'BYOVPN_Server'},
                                vpc_security_group_ids=[secgrp.id],
                                user_data=user_data_script)

    pulumi.export("public_ip", instance.public_ip)

def write_sudo_file(filepath : str, content : str) -> bool:
    """
    Writes a string to a protected file by piping it through `sudo tee`.
    """
    print(f"\nRequesting sudo privileges to write to {filepath}...")
    
    try:
        process = subprocess.Popen(
            ['sudo', 'tee', filepath], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.DEVNULL, # Hides the output so it doesn't flood your terminal
            stderr=subprocess.PIPE
        )
        
        _, stderr = process.communicate(input=content.encode('utf-8'))
        
        if process.returncode != 0:
            print(f"Error writing to {filepath}: {stderr.decode('utf-8').strip()}")
            return False
            
        return True
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False