from typing import Tuple
from jinja2 import FileSystemLoader, Environment
import pulumi.automation as auto

import keyring
import requests
import secrets
import subprocess
import sys


def generate_key_pair() -> Tuple[str, str]:
    """Generates a WireGuard key pair using the wg command-line tool in the form (private_key, public_key)."""
    private_key = subprocess.check_output(['wg', 'genkey']).decode('utf-8').strip()
    public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode('utf-8')).decode('utf-8').strip()
    return private_key, public_key


def generate_client_config(server_listen_port: int, client_private_key: str, server_public_key: str,
                           server_public_ip: str, allowed_ips: str) -> str:
    """Renders and returns the WireGuard client configuration as a string."""
    env = Environment(loader=FileSystemLoader("wg-conf"))
    
    template = env.get_template("client.conf.j2")
    return template.render(
        server_listen_port=server_listen_port,
        client_private_key=client_private_key,
        server_public_key=server_public_key,
        server_public_ip=server_public_ip,
        allowed_ips=allowed_ips
    )

def generate_server_config(server_listen_port: int, server_private_key: str, client_public_key: str) -> str:
    """Renders and returns the WireGuard server configuration as a string."""
    env = Environment(loader=FileSystemLoader("wg-conf"))
    
    template = env.get_template("wg0.conf.j2")
    return template.render(
        server_listen_port=server_listen_port,
        server_private_key=server_private_key,
        client_public_key=client_public_key
    )


def get_public_ip() -> str:
    url = "https://ipv4.icanhazip.com/"
    try:
        response = requests.get(url)
        public_ip = response.text.strip()
        return public_ip
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP: {e}")
        return None
    

def stack_destroy_and_exit(stack: auto.Stack, message: str | None = None):
    if message:
        print(message)
    stack.destroy(on_output=lambda out: print(f"Pulumi Output: {out}"))
    print("Exiting program.")
    sys.exit(0)

def get_or_create_keyring_password(service_name: str, username: str) -> str:
    """Retrieves a password from the keyring, or creates and stores one if it doesn't exist."""
    password = keyring.get_password(service_name, username)
    if password is None:
        password = secrets.token_urlsafe(32)
        keyring.set_password(service_name, username, password)
    return password


def write_sudo_file(filepath : str, content : str) -> int:
    """
    Writes a string to a protected file by piping it through `sudo tee`.
    Returns 0 on success, non-zero on failure.
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
            return 1  # Sudo failed
            
        return 0  # Success
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 2  # Unexpected error
