from aws import check_aws_login, launch_byovpn_ec2
from util import generate_key_pair

import argparse
from functools import partial
import pulumi.automation as auto


def main():
    """Launches the BYOVPN Instance and configures the client to connect."""
    parser = argparse.ArgumentParser(
        description="Launch a BYOVPN WireGuard server on AWS and generate client configuration.",
    )
    parser.add_argument("-p", "--port", type=int, default=33333, help="Port for the WireGuard server to listen on.")
    parser.add_argument("--fetch-client-ip", action="store_true", help="Whether to fetch the client's public IP for allowed IPs.")
    args = parser.parse_args()

    if not check_aws_login():
        print("AWS credentials not found or invalid. Please configure your AWS credentials and try again.")
        return

    client_private_key, client_public_key = generate_key_pair()
    server_private_key, server_public_key = generate_key_pair()
    
    def pulumi_program_byovpn_ec2():
        """
        Pulumi's automation API only takes in parameterless functions, aka PulumiFn's.
        This function bakes in the arguments of the function `launch_byovpn_ec2`.
        """
        return partial(launch_byovpn_ec2,
                       server_port=args.port,
                       server_private_key=server_private_key,
                       client_public_key=client_public_key,
                       fetch_client_ip=args.fetch_client_ip)

    pulumi_program = pulumi_program_byovpn_ec2()
    stack = auto.create_or_select_stack(stack_name="byovpn-aws",
                                project_name="byovpn",
                                program=pulumi_program)
    stack.set_config("aws:region", auto.ConfigValue(value="us-east-1"))

    stack.up(on_output=lambda out: print(f"Pulumi Output: {out}"))



if __name__ == "__main__":
    main()