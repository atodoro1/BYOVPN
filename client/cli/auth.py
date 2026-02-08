"""Cloud provider credential management CLI commands."""

import os
from typing import Annotated, Optional
from pathlib import Path
import configparser
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
import typer

from db.connection import init_db
from services.credential_service import CredentialService
from providers import get_provider, list_providers

app = typer.Typer(no_args_is_help=True)
console = Console()
service = CredentialService()

# Initialize database on import
init_db()


def get_aws_credentials_from_file(profile: str = "default") -> dict[str, str]:
    """Read AWS credentials from ~/.aws/credentials file.

    Args:
        profile: AWS profile name to read (default: "default")

    Returns:
        Dict with aws_access_key_id, aws_secret_access_key, and optionally aws_session_token
    """
    credentials_file = Path.home() / ".aws" / "credentials"

    if not credentials_file.exists():
        return {}

    try:
        config = configparser.ConfigParser()
        config.read(credentials_file)

        if profile not in config:
            return {}

        creds = {}
        profile_data = config[profile]

        if "aws_access_key_id" in profile_data:
            creds["ACCESS_KEY_ID"] = profile_data["aws_access_key_id"]
        if "aws_secret_access_key" in profile_data:
            creds["SECRET_ACCESS_KEY"] = profile_data["aws_secret_access_key"]
        if "aws_session_token" in profile_data:
            creds["SESSION_TOKEN"] = profile_data["aws_session_token"]

        return creds
    except Exception:
        return {}


@app.command()
def add(
    provider: Annotated[str, typer.Argument(help="Cloud provider (hetzner, aws)")],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Name of the credential set")] = None,
    test: Annotated[bool, typer.Option("--test/--no-test", help="Test the credentials after adding")] = True
) -> None:
    """Add a new cloud provider credential.

    Credentials are stored securely using environment variables.
    The database stores only metadata (names, timestamps, test results).

    Examples:
        vpn auth add hetzner
        vpn auth add aws --name production --test
    """
    if not name:
        name = provider

    # Validate provider
    try:
        provider_impl = get_provider(provider)
    except ValueError:
        console.print(f"[red]Error:[/red] Unsupported provider '{provider}'")
        console.print(f"[dim]Supported providers: {', '.join(list_providers())}[/dim]")
        raise typer.Exit(1)

    # Prompt for credential values
    fields = provider_impl.get_env_var_fields()
    credentials = {}

    console.print(f"\n[bold]Adding {provider} credentials: {name}[/bold]\n")

    # Generate env var prefix to check for existing vars
    safe_name = name.upper().replace('-', '_').replace(' ', '_')
    env_var_prefix = f"BYOVPN_CRED_{safe_name}"

    # For AWS, check ~/.aws/credentials file
    aws_file_creds = {}
    if provider == "aws":
        aws_file_creds = get_aws_credentials_from_file()
        if aws_file_creds:
            console.print("[cyan]Found AWS credentials in ~/.aws/credentials (default profile)[/cyan]")

    for field in fields:
        env_var = f"{env_var_prefix}_{field}"
        existing_value = os.environ.get(env_var)
        aws_file_value = aws_file_creds.get(field)

        # Check if env var already exists
        if existing_value:
            console.print(f"[cyan]Found existing environment variable:[/cyan] {env_var}")
            use_existing = Confirm.ask(
                f"Use existing value for {field}?",
                default=True
            )

            if use_existing:
                credentials[field] = existing_value
                console.print(f"  [green]✓[/green] Using existing value from {env_var}")
                continue

        # Check if AWS credentials file has this field
        elif aws_file_value:
            console.print(f"[cyan]Found {field} in ~/.aws/credentials[/cyan]")
            use_aws_file = Confirm.ask(
                f"Use value from ~/.aws/credentials for {field}?",
                default=True
            )

            if use_aws_file:
                credentials[field] = aws_file_value
                console.print("  [green]✓[/green] Using value from ~/.aws/credentials")
                continue

        # Prompt for new value
        if field == "SESSION_TOKEN":
            # Optional for AWS
            value = Prompt.ask(
                f"{field} (optional, press Enter to skip)",
                password=True,
                default=""
            )
        else:
            value = Prompt.ask(field, password=True)

        if value:
            credentials[field] = value

    # Add to database
    try:
        cred = service.add_credential(name, provider, credentials, test=test)

        console.print(f"\n[green]✓[/green] Credential '{name}' added to database")

        # Access test results if available (handle potential detached state)
        try:
            if test and cred.test_status == "success":
                console.print("[green]✓[/green] Credentials tested successfully")
                if cred.test_message:
                    console.print(f"  {cred.test_message}")
            elif test and cred.test_status == "failed":
                console.print("[red]✗[/red] Credential test failed")
                console.print(f"  {cred.test_message}")
        except Exception:
            # If we can't access the credential object (detached), skip test status display
            pass

        # Show env var instructions
        # Use the env_var_prefix we already calculated earlier
        vars_already_set = []
        vars_need_setting = []

        for field in fields:
            if field in credentials:
                env_var = f"{env_var_prefix}_{field}"
                if os.environ.get(env_var) == credentials[field]:
                    vars_already_set.append(env_var)
                else:
                    vars_need_setting.append((env_var, credentials[field]))

        if vars_already_set:
            console.print("\n[green]✓[/green] Environment variables already set:")
            for var in vars_already_set:
                console.print(f"  {var}")

        if vars_need_setting:
            console.print("\n[bold yellow]⚠ Important:[/bold yellow] Set these environment variables:")
            console.print()
            for env_var, value in vars_need_setting:
                console.print(f"  export {env_var}='{value}'")
            console.print("\n[dim]Add these to ~/.bashrc or ~/.zshrc to persist across sessions[/dim]")
        elif not vars_already_set:
            console.print("\n[dim]No environment variables needed (optional fields were skipped)[/dim]")

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def list(
    provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="Filter by cloud provider")] = None,
    format: Annotated[str, typer.Option("--format", help="Output format (table, json, yaml)")] = "table"
) -> None:
    """List all saved cloud provider credentials.

    Shows metadata only - actual credential values are in environment variables.

    Examples:
        vpn auth list
        vpn auth list --provider hetzner
        vpn auth list --format json
    """
    try:
        credentials = service.list_credentials(provider=provider)

        if not credentials:
            if provider:
                console.print(f"[yellow]No credentials found for {provider}[/yellow]")
            else:
                console.print("[yellow]No credentials configured[/yellow]")
                console.print("\n[dim]Add credentials with: vpn auth add <provider>[/dim]")
            return

        if format == "json":
            import json
            data = [{
                "name": c.name,
                "provider": c.provider,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "last_used": c.last_used.isoformat() if c.last_used else None,
                "last_tested": c.last_tested.isoformat() if c.last_tested else None,
                "test_status": c.test_status
            } for c in credentials]
            console.print(json.dumps(data, indent=2))

        elif format == "yaml":
            import yaml
            data = [{
                "name": c.name,
                "provider": c.provider,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "last_used": c.last_used.isoformat() if c.last_used else None,
                "last_tested": c.last_tested.isoformat() if c.last_tested else None,
                "test_status": c.test_status
            } for c in credentials]
            console.print(yaml.dump(data, default_flow_style=False))

        else:  # table
            table = Table(title="Saved Credentials")
            table.add_column("Name", style="cyan")
            table.add_column("Provider", style="magenta")
            table.add_column("Created", style="dim")
            table.add_column("Last Used", style="dim")
            table.add_column("Status", style="green")

            for cred in credentials:
                # Format timestamps
                created = cred.created_at.strftime("%Y-%m-%d %H:%M") if cred.created_at else "Unknown"
                last_used = cred.last_used.strftime("%Y-%m-%d %H:%M") if cred.last_used else "Never"

                # Format status
                if cred.test_status:
                    status = "✓ Tested" if cred.test_status == "success" else "✗ Failed"
                else:
                    status = "Not tested"

                table.add_row(
                    cred.name,
                    cred.provider,
                    created,
                    last_used,
                    status
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def remove(
    name: Annotated[str, typer.Argument(help="Credential name to remove")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Force removal without confirmation")] = False
) -> None:
    """Remove a cloud provider credential.

    This only removes the database entry - you should also remove the
    environment variables from your shell configuration.

    Examples:
        vpn auth remove production
        vpn auth remove dev --force
    """
    # Confirm removal
    if not force:
        console.print(f"[yellow]Warning:[/yellow] This will remove credentials for '{name}'")
        console.print("[dim]The environment variables will NOT be automatically removed.[/dim]")

        if not Confirm.ask("Continue?", default=False):
            console.print("Operation cancelled.")
            return

    try:
        # Get credential to show env vars to remove
        cred = service.get_credential(name)
        if cred:
            provider_impl = get_provider(cred.provider)
            fields = provider_impl.get_env_var_fields()

            # Remove from database
            service.remove_credential(name)

            console.print(f"[green]✓[/green] Credentials for '{name}' have been removed from database")

            # Show instructions to remove env vars
            console.print("\n[yellow]Don't forget to remove environment variables:[/yellow]")
            for field in fields:
                env_var = f"{cred.env_var_prefix}_{field}"
                console.print(f"  unset {env_var}")
            console.print("\n[dim]Remove the export lines from ~/.bashrc or ~/.zshrc[/dim]")
        else:
            console.print(f"[red]Error:[/red] Credential '{name}' not found")
            raise typer.Exit(1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("[dim]Use 'vpn auth list' to see available credentials[/dim]")
        raise typer.Exit(1)


@app.command()
def test(
    name: Annotated[str, typer.Argument(help="Credential name to test")]
) -> None:
    """Test the credentials for a specific cloud provider.

    Reads credentials from environment variables and tests with the provider's API.

    Examples:
        vpn auth test production
        vpn auth test aws-main
    """
    console.print(f"[cyan]Testing credentials for '{name}'...[/cyan]")

    try:
        success, message = service.test_credential(name)

        if success:
            console.print(f"[green]✓[/green] Credentials are valid")
            console.print(f"  {message}")
        else:
            console.print(f"[red]✗[/red] Credentials are invalid")
            console.print(f"  {message}")
            raise typer.Exit(1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
