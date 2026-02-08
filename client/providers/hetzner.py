"""Hetzner Cloud provider implementation."""

import httpx
from typing import Dict, List
from providers.base import BaseProvider, TestResult


class HetznerProvider(BaseProvider):
    """Hetzner Cloud provider."""

    def get_env_var_fields(self) -> List[str]:
        """Hetzner requires a single API token."""
        return ["TOKEN"]

    def test_credentials(self, credentials: Dict[str, str]) -> TestResult:
        """Test Hetzner API token by making API call.

        Args:
            credentials: Dict with "TOKEN" key

        Returns:
            TestResult indicating success/failure
        """
        token = credentials.get("TOKEN")
        if not token:
            return TestResult(success=False, message="Token not provided")

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = httpx.get(
                "https://api.hetzner.cloud/v1/datacenters",
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                return TestResult(
                    success=True,
                    message="Successfully authenticated with Hetzner Cloud"
                )
            elif response.status_code == 401:
                return TestResult(success=False, message="Invalid API token")
            else:
                return TestResult(
                    success=False,
                    message=f"API returned status {response.status_code}"
                )
        except httpx.TimeoutException:
            return TestResult(
                success=False,
                message="Request timed out - check your internet connection"
            )
        except Exception as e:
            return TestResult(success=False, message=f"Test failed: {str(e)}")
