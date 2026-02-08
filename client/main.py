import typer

import cli.auth
import cli.server
import cli.connection
import cli.apps
import cli.config
import cli.utils
import cli.advanced

app = typer.Typer(no_args_is_help=True)

# Command groups (vpn <group> <subcommand>)
app.add_typer(cli.auth.app, name="auth", help="Manage cloud provider credentials")
app.add_typer(cli.apps.app, name="apps", help="Manage VPN server applications")
app.add_typer(cli.config.app, name="config", help="Manage CLI configuration settings")

# Server management (vpn server <subcommand>)
app.add_typer(cli.server.app, name="server", help="Manage VPN servers")

# Connection management (vpn connection <subcommand>)
app.add_typer(cli.connection.app, name="connection", help="Manage VPN connections")

# Utilities and diagnostics (vpn utils <subcommand>)
app.add_typer(cli.utils.app, name="utils", help="Utilities and diagnostics")

# Advanced features (vpn advanced <subcommand>)
app.add_typer(cli.advanced.app, name="advanced", help="Advanced features (Phase 3+)")

if __name__ == "__main__":
    app()
