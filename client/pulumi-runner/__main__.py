"""An AWS Python Pulumi program"""

from util import *

import os
import time
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


server_private_key, server_public_key = generate_key_pair()
client_private_key, client_public_key = generate_key_pair()

server_config = generate_server_config(WG_SERVER_PORT, server_private_key, client_public_key)

# Adding the user data script to install WireGuard on the EC2 instance
user_data_script = f"""#!/usr/bin/env bash
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

# Create an AWS resource (EC2 Instance)
instance = aws.ec2.Instance('web-server-vpn',
    instance_type='t3.micro',
    ami=ubuntu.id,
    tags={'Name': 'VPN_Server'},
    vpc_security_group_ids=[group.id],
    user_data=user_data_script)

server_public_ip = instance.public_ip
client_public_ip = get_public_ip()

client_config = generate_client_config(WG_SERVER_PORT, client_private_key, 
                                       server_public_key, server_public_ip, f"{client_public_ip}/32")

with open("/etc/wireguard/client.conf", "w") as f:
    f.write(client_config)

os.chmod("/etc/wireguard/client.conf", 600)


# Wait until the instance is running before trying to bring up the WireGuard interface
while True:
    instance_state = aws.ec2.get_instance(instance_id=instance.id).state
    if instance_state == "running":
        break
    time.sleep(5)

os.system("wg-quick up client.conf")


# Export the ID of the instance
pulumi.export('instance_id', instance.id)
pulumi.export('publicIP', instance.public_ip)
pulumi.export('publicHostName', instance.public_dns)