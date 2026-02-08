from typing import Annotated, Optional
from rich import print

import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def create(
    provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="Cloud provider (hetzner, digitalocean, aws, gcp, vultr, oracle)")] = None,
    credentials: Annotated[Optional[str], typer.Option("--credentials", help="Specific credential set to use")] = None,
    region: Annotated[Optional[str], typer.Option("--region", "-r", help="Region/location code")] = None,
    list_regions: Annotated[bool, typer.Option("--list-regions", help="Show available regions and exit")] = False,
    size: Annotated[str, typer.Option("--size", help="Predefined server size (small, medium, large)")] = "small",
    instance_type: Annotated[Optional[str], typer.Option("--instance-type", help="Provider-specific instance type")] = None,
    config: Annotated[Optional[str], typer.Option("--config", help="YAML config file with server settings")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Friendly server name")] = None,
    connect: Annotated[bool, typer.Option("--connect", help="Connect to VPN immediately after creation")] = False,
    no_connect: Annotated[bool, typer.Option("--no-connect", help="Don't auto-connect")] = True
) -> None:
    """
    Create and provision a new VPN server.
    """
    print("Not Fully Implemented")

@app.command()
def list(
    provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="Filter by cloud provider")] = None,
    region: Annotated[Optional[str], typer.Option("--region", "-r", help="Filter by region")] = None,
    status: Annotated[Optional[str], typer.Option("--status", help="Filter by status (provisioning, ready, connected, stopped, error)")] = None,
    sort: Annotated[str, typer.Option("--sort", help="Sort by field (created, name, region, cost, status)")] = "created",
    format: Annotated[str, typer.Option("--format", help="Output format (table, json, yaml)")] = "table"
) -> None:
    """
    List all VPN servers.
    """
    print("Not Fully Implemented")

@app.command()
def info(
    server_id: Annotated[Optional[str], typer.Argument(help="Server ID to show info for")] = None,
    current: Annotated[bool, typer.Option("--current", help="Show info for currently connected server")] = False,
    format: Annotated[str, typer.Option("--format", help="Output format (table, json, yaml)")] = "table"
) -> None:
    """
    Show detailed information about a server.
    """
    print("Not Fully Implemented")

@app.command()
def destroy(
    server_id: Annotated[str, typer.Argument(help="Server ID to destroy")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False,
    keep_pulumi: Annotated[bool, typer.Option("--keep-pulumi", help="Don't delete pulumi state files")] = False,
    disconnect: Annotated[bool, typer.Option("--disconnect", help="Disconnect first if connected")] = True
) -> None:
    """
    Permanently delete a VPN server and all resources.
    """
    print("Not Fully Implemented")

@app.command()
def start(
    server_id: Annotated[str, typer.Argument(help="Server ID to start")]
) -> None:
    """
    Start a stopped server. (Later feature)
    """
    print("Not Fully Implemented")

@app.command()
def stop(
    server_id: Annotated[str, typer.Argument(help="Server ID to stop")],
    disconnect: Annotated[bool, typer.Option("--disconnect", help="Disconnect VPN first")] = True
) -> None:
    """
    Stop a running server without destroying. (Later feature)
    """
    print("Not Fully Implemented")
