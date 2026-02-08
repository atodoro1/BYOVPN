from typing import Annotated
from rich import print


import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def add(provider: str, 
        name: Annotated[str, typer.Option("--name", "-n", help="Name of the credential set")],
        token: Annotated[str, typer.Option("--token", "-t", help="API token (if not provided, prompts securely)")],
        from_env: Annotated[bool, typer.Option("--from-env", help="Load credentials from environment variables")],
        test: Annotated[bool, typer.Option("--test", help="Test the credentials after adding")]) -> None:
    """
    Add a new cloud provider to the configuration.
    """
    # Implementation for adding a new cloud provider goes here
    print("Not Fully Implemented")

@app.command()
def list(provider: Annotated[str, typer.Option("--provider", "-p", help="Cloud provider to list credentials for")]) -> None:
    """
    List all configured cloud providers.
    """
    # Implementation for listing cloud providers goes here
    print("Not Fully Implemented")

@app.command()
def remove(name: str, 
           force: Annotated[
        bool, typer.Option(prompt="Are you sure you want to remove this credential?", help="Force removal without confirmation")]
        ) -> None:
    """
    Remove a cloud provider from the configuration by name.
    """

    # Implementation for removing a cloud provider goes here
    print(f"Warning: This will remove credentials for {name}.")

    if force:
        # Code to remove the provider goes here
        print(f"Credentials for {name} have been removed.")
    else:
        print("Operation cancelled.")

    print("Not Fully Implemented")

@app.command()
def test(name: str) -> None:
    """
    Test the credentials for a specific cloud provider by name.
    """
    # Implementation for testing credentials goes here
    print("Not Fully Implemented")

    