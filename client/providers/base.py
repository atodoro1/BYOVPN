"""Base provider class for cloud providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel


class TestResult(BaseModel):
    """Result of credential test."""
    success: bool
    message: str
    details: Dict[str, Any] = {}


class BaseProvider(ABC):
    """Base class for cloud provider implementations."""

    @abstractmethod
    def get_env_var_fields(self) -> List[str]:
        """Return list of env var field names needed.

        Returns:
            List of field names (e.g., ["TOKEN"] for Hetzner)
        """
        pass

    @abstractmethod
    def test_credentials(self, credentials: Dict[str, str]) -> TestResult:
        """Test if credentials are valid.

        Args:
            credentials: Dict mapping field names to values

        Returns:
            TestResult with success status and message
        """
        pass

    def get_env_var_name(self, credential_name: str, field: str) -> str:
        """Generate environment variable name.

        Args:
            credential_name: User-provided credential name
            field: Field name (e.g., "TOKEN")

        Returns:
            Environment variable name (e.g., "BYOVPN_CRED_PRODUCTION_TOKEN")
        """
        safe_name = credential_name.upper().replace('-', '_').replace(' ', '_')
        safe_field = field.upper().replace('-', '_')
        return f"BYOVPN_CRED_{safe_name}_{safe_field}"
