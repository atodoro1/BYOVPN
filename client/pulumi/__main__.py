"""An AWS Python Pulumi program"""

from tokenize import group
from turtle import pu

import pulumi
import pulumi_aws as aws


# Temp globals for testing
WG_SERVER_PORT = 33333

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

group = aws.ec2.SecurityGroup('web-secgrp', 
                              description='Enable WireGuard VPN access',
                                ingress=[
                                    {'protocol': 'udp', 'to_port': WG_SERVER_PORT, 'from_port': 0, 'cidr_blocks': ['0.0.0.0/0']}])


# Adding the user data script to install WireGuard on the EC2 instance
user_data_script = f"""#!/usr/bin/env bash
sudo apt-get update
sudo apt install -y  wireguard wireguard-tools openresolv
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
"""


# Create an AWS resource (EC2 Instance)
instance = aws.ec2.Instance('web-server-vpn',
    instance_type='t3.micro',
    ami=ubuntu.id,
    tags={'Name': 'VPN_Server'},
    vpc_security_group_ids=[group.id],)

# Export the ID of the instance
pulumi.export('instance_id', instance.id)
pulumi.export('publicIP', instance.public_ip)
pulumi.export('publicHostName', instance.public_dns)