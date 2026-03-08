from aws import check_aws_login, launch_byovpn_ec2
from util import generate_client_config, generate_key_pair, get_or_create_keyring_password, get_public_ip, stack_destroy_and_exit, write_sudo_file

import argparse
import pulumi.automation as auto
import os
import sys


SUPPORTED_PROVIDERS = ["aws"]

# Exit codes for write_client_config
WRITE_SUCCESS = 0
WRITE_FILE_EXISTS_USER_DECLINED = 1
WRITE_FILE_EXISTS_INVALID_INPUT = 2
WRITE_SUDO_FAILED = 3


def _print_stack_warning(provider: str):
    """Prints a warning that the Pulumi stack is still running and provides destroy command."""
    print(f"\nNote: Your Pulumi stack 'byovpn-{provider}' is still active.")
    print(f"To clean up resources, run: python main.py --provider {provider} --destroy")


def launch_aws(port: int, server_private_key: str, client_public_key: str, allowed_ips: str, stack_name: str) ->  str:
    """Launches the BYOVPN server on AWS using Pulumi's automation API. Returns the public IP of the launched server."""
    if not check_aws_login():
        print("AWS credentials not found or invalid. Please configure your AWS credentials and try again.")
        sys.exit(1)

    def pulumi_program_byovpn_ec2():
        """
        Pulumi's automation API only takes in parameterless functions, aka PulumiFn's.
        This function bakes in the arguments of the function `launch_byovpn_ec2`.
        """
        launch_byovpn_ec2(server_port=port,
                        server_private_key=server_private_key,
                        client_public_key=client_public_key,
                        allowed_ips=allowed_ips)
        
    pulumi_program = pulumi_program_byovpn_ec2
    stack = auto.create_or_select_stack(stack_name=stack_name,
                                project_name="byovpn",
                                program=pulumi_program)
    stack.set_config("aws:region", auto.ConfigValue(value="us-east-1"))
    stack.refresh(on_output=print)
    up_result = stack.up(on_output=lambda out: print(f"Pulumi Output: {out}"))

    server_ip = up_result.outputs["public_ip"].value
    print(f"BYOVPN server launched with public IP: {server_ip}")

    return server_ip


def write_client_config(port: int, client_private_key: str, server_public_key: str, server_ip: str, allowed_ips: str, client_config_path: str) -> int:
    """Writes client config to disk. Returns error code (0 for success)."""
    client_config = generate_client_config(port, client_private_key, server_public_key, server_ip, allowed_ips)
    
    print("\n--- Generated Client Configuration ---")
    print(client_config)
    print("--- End Configuration ---\n")

    if os.path.exists(client_config_path):
        print(f"Warning: {client_config_path} already exists.")
        read = input("Do you want to overwrite it? (y/n): ")
        if read.lower() == "n":
            return WRITE_FILE_EXISTS_USER_DECLINED
        elif read.lower() != "y":
            return WRITE_FILE_EXISTS_INVALID_INPUT
        print(f"Overwriting {client_config_path} with new client configuration.")
   
    write_status = write_sudo_file(client_config_path, client_config)
    if write_status != 0:
        return WRITE_SUDO_FAILED
    
    return WRITE_SUCCESS


def main():
    """
    Launches the BYOVPN Instance and configures the client to connect.
    Stack naming convention: byovpn-<provider>, e.g. byovpn-aws.
    """
    parser = argparse.ArgumentParser(
        description="Launch a BYOVPN WireGuard server on AWS and generate client configuration.",
    )
    parser.add_argument("-p", "--port", type=int, default=33333, help="Port for the WireGuard server to listen on.")
    parser.add_argument("--fetch-client-ip", action="store_true", help="Whether to fetch the client's public IP for allowed IPs.")
    parser.add_argument("--provider", type=str, help="Cloud provider to use for launching the BYOVPN server. Currently only 'aws' is supported.")
    parser.add_argument("--client-config-path", type=str, default="/etc/wireguard/client.conf", help="Path to write the client configuration file (default: /etc/wireguard/client.conf).")
    parser.add_argument("-d", "--destroy", action="store_true", help="Terminate the BYOVPN server.")
    args = parser.parse_args()

    if args.provider not in SUPPORTED_PROVIDERS:
        print(f"Error: Unsupported provider '{args.provider}'. Supported providers are: {', '.join(SUPPORTED_PROVIDERS)}.")
        sys.exit(1)

    stack_name = f"byovpn-{args.provider}"
    current_user = os.getenv("USER")
    os.environ["PULUMI_CONFIG_PASSPHRASE"] = get_or_create_keyring_password(stack_name, current_user)

    if args.destroy:
        # Since it's an inline program, we just pass a dummy function
        # to satisfy the API's requirement for a 'program' argument.
        def dummy_program():
            pass

        stack = auto.select_stack(
            stack_name=stack_name, 
            project_name="byovpn", 
            program=dummy_program
        )
        stack_destroy_and_exit(stack)

    allowed_ips = "0.0.0.0/0"
    if args.fetch_client_ip:
        client_ip = get_public_ip()
        allowed_ips = f"{client_ip}/32"

    client_private_key, client_public_key = generate_key_pair()
    server_private_key, server_public_key = generate_key_pair()

    if args.provider == "aws":
        server_ip = launch_aws(args.port, server_private_key, client_public_key, allowed_ips, stack_name)

    write_status = write_client_config(args.port, client_private_key, server_public_key, server_ip, allowed_ips, args.client_config_path)
    
    if write_status == WRITE_FILE_EXISTS_USER_DECLINED:
        print("User declined to overwrite existing client configuration.")
        _print_stack_warning(args.provider)
        sys.exit(1)
    elif write_status == WRITE_FILE_EXISTS_INVALID_INPUT:
        print("Invalid input for overwrite prompt.")
        _print_stack_warning(args.provider)
        sys.exit(1)
    elif write_status == WRITE_SUDO_FAILED:
        print("Failed to write client configuration with sudo.")
        _print_stack_warning(args.provider)
        sys.exit(1)
    elif write_status != WRITE_SUCCESS:
        print(f"Unknown error writing client configuration (code {write_status}).")
        _print_stack_warning(args.provider)
        sys.exit(1)

    print(f"Your client configuration has been generated and saved to {args.client_config_path}.")
    print("You can use this configuration file to connect to your BYOVPN WireGuard server by running `wg-quick up client`.")
    print("To disconnect, run `wg-quick down client`.")


if __name__ == "__main__":
    main()