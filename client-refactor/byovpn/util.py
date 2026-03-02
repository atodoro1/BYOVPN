from typing import Tuple
from jinja2 import Template
import pulumi.automation as auto

import keyring
import requests
import secrets
import subprocess


def generate_key_pair() -> Tuple[str, str]:
    """Generates a WireGuard key pair using the wg command-line tool in the form (private_key, public_key)."""
    private_key = subprocess.check_output(['wg', 'genkey']).decode('utf-8').strip()
    public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode('utf-8')).decode('utf-8').strip()
    return private_key, public_key


def generate_client_config(server_listen_port: int, client_private_key: str, server_public_key: str,
                        server_public_ip: str, allowed_ips: str) -> str:
    """Writes the WireGuard client configuration to a file."""
    template_config = open("wg-conf/client.conf.j2")
    rendered = Template(template_config.read()).render({"server_listen_port": server_listen_port,
                                                        "client_private_key": client_private_key,
                                                        "server_public_key": server_public_key,
                                                        "server_public_ip": server_public_ip,
                                                        "allowed_ips": allowed_ips})
    return rendered


def generate_server_config(server_listen_port: int, server_private_key: str, client_public_key: str) -> str:
    """Writes the WireGuard server configuration to a file."""
    template_config = open("wg-conf/wg0.conf.j2")
    rendered = Template(template_config.read()).render({"server_listen_port": server_listen_port,
                                                        "server_private_key": server_private_key,
                                                        "client_public_key": client_public_key})
    return rendered


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
    exit(0)

def get_or_create_keyring_password(service_name: str, username: str) -> str:
    """Retrieves a password from the keyring, or creates and stores one if it doesn't exist."""
    password = keyring.get_password(service_name, username)
    if password is None:
        password = secrets.token_urlsafe(32)
        keyring.set_password(service_name, username, password)
    return password