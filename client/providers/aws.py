"""AWS provider implementation.

Note: AWS credentials are passed to Pulumi for provisioning.
This provider only does basic format validation - Pulumi handles actual AWS authentication.
"""

from typing import Dict, List
from providers.base import BaseProvider, TestResult


class AWSProvider(BaseProvider):
    """AWS provider (uses Pulumi for provisioning)."""

    def get_env_var_fields(self) -> List[str]:
        """AWS requires access key ID and secret access key.

        SESSION_TOKEN is optional for temporary credentials.
        """
        return ["ACCESS_KEY_ID", "SECRET_ACCESS_KEY", "SESSION_TOKEN"]

    def test_credentials(self, credentials: Dict[str, str]) -> TestResult:
        """Validate AWS credentials format.

        Actual AWS API testing will be handled by Pulumi during provisioning.

        Args:
            credentials: Dict with AWS credential fields

        Returns:
            TestResult with format validation results
        """
        access_key = credentials.get("ACCESS_KEY_ID")
        secret_key = credentials.get("SECRET_ACCESS_KEY")

        if not access_key or not secret_key:
            return TestResult(
                success=False,
                message="AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY required"
            )

        # Basic format validation
        if not access_key.startswith("AKIA"):
            return TestResult(
                success=False,
                message="AWS_ACCESS_KEY_ID should start with 'AKIA'"
            )

        if len(secret_key) < 40:
            return TestResult(
                success=False,
                message="AWS_SECRET_ACCESS_KEY seems too short (should be 40 characters)"
            )

        return TestResult(
            success=True,
            message="AWS credentials validated (format check only - Pulumi will test during provisioning)"
        )
