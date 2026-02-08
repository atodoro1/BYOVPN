"""Cloud provider implementations."""

from providers.base import BaseProvider
from providers.hetzner import HetznerProvider
from providers.aws import AWSProvider

PROVIDER_REGISTRY = {
    "hetzner": HetznerProvider,
    "aws": AWSProvider,
}


def get_provider(provider_name: str) -> BaseProvider:
    """Get provider instance."""
    if provider_name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return PROVIDER_REGISTRY[provider_name]()


def list_providers() -> list[str]:
    """List all supported providers."""
    return list(PROVIDER_REGISTRY.keys())
