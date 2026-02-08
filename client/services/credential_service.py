"""Credential management service.

High-level business logic for managing cloud provider credentials.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import configparser

from db.connection import get_db
from db.models import CloudCredential
from providers import get_provider


def _get_aws_credentials_from_file(profile: str = "default") -> Dict[str, str]:
    """Read AWS credentials from ~/.aws/credentials file.

    Args:
        profile: AWS profile name to read (default: "default")

    Returns:
        Dict with ACCESS_KEY_ID, SECRET_ACCESS_KEY, and optionally SESSION_TOKEN
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


class CredentialService:
    """High-level credential management."""

    def add_credential(
        self,
        name: str,
        provider: str,
        credentials: Dict[str, str],
        test: bool = False
    ) -> CloudCredential:
        """Add a new credential.

        Args:
            name: Friendly name for credential set
            provider: Cloud provider ("hetzner" or "aws")
            credentials: Dict mapping field names to values
            test: Whether to test credentials after adding

        Returns:
            Created CloudCredential instance

        Raises:
            ValueError: If credential already exists or test fails
        """
        # Validate provider
        provider_impl = get_provider(provider)

        # Check if name already exists
        with get_db() as db:
            existing = db.query(CloudCredential).filter_by(name=name).first()
            if existing:
                raise ValueError(f"Credential '{name}' already exists")

            # Test if requested
            test_status = None
            test_message = None
            if test:
                result = provider_impl.test_credentials(credentials)
                test_status = "success" if result.success else "failed"
                test_message = result.message
                if not result.success:
                    raise ValueError(f"Credential test failed: {result.message}")

            # Generate env var prefix
            safe_name = name.upper().replace('-', '_').replace(' ', '_')
            env_var_prefix = f"BYOVPN_CRED_{safe_name}"

            # Create credential record
            cred = CloudCredential(
                name=name,
                provider=provider,
                env_var_prefix=env_var_prefix,
                created_at=datetime.utcnow(),
                last_tested=datetime.utcnow() if test else None,
                test_status=test_status,
                test_message=test_message
            )

            db.add(cred)
            db.commit()
            db.refresh(cred)

            return cred

    def get_credential(self, name: str) -> Optional[CloudCredential]:
        """Get credential by name.

        Args:
            name: Credential name

        Returns:
            CloudCredential instance (detached from session) or None if not found
        """
        with get_db() as db:
            cred = db.query(CloudCredential).filter_by(name=name).first()

            if cred:
                # Force load all attributes before session closes
                _ = cred.id
                _ = cred.name
                _ = cred.provider
                _ = cred.env_var_prefix
                _ = cred.created_at
                _ = cred.last_used
                _ = cred.last_tested
                _ = cred.test_status
                _ = cred.test_message

                # Detach from session
                db.expunge(cred)

            return cred

    def list_credentials(self, provider: Optional[str] = None) -> List[CloudCredential]:
        """List all credentials.

        Args:
            provider: Filter by provider (optional)

        Returns:
            List of CloudCredential instances (detached from session)
        """
        with get_db() as db:
            query = db.query(CloudCredential)
            if provider:
                query = query.filter_by(provider=provider)
            credentials = query.all()

            # Force load all attributes before session closes
            for cred in credentials:
                # Access all attributes to load them into the object's __dict__
                _ = cred.id
                _ = cred.name
                _ = cred.provider
                _ = cred.env_var_prefix
                _ = cred.created_at
                _ = cred.last_used
                _ = cred.last_tested
                _ = cred.test_status
                _ = cred.test_message

            # Detach from session
            db.expunge_all()

            return credentials

    def remove_credential(self, name: str) -> None:
        """Remove credential.

        Args:
            name: Credential name

        Raises:
            ValueError: If credential not found
        """
        with get_db() as db:
            cred = db.query(CloudCredential).filter_by(name=name).first()
            if not cred:
                raise ValueError(f"Credential '{name}' not found")
            db.delete(cred)
            db.commit()

    def get_credential_values(self, name: str) -> Dict[str, str]:
        """Load credential values from environment variables.

        For AWS credentials, falls back to ~/.aws/credentials if env vars not set.

        Args:
            name: Credential name

        Returns:
            Dict mapping field names to values from environment or AWS file

        Raises:
            ValueError: If credential not found or values missing
        """
        cred = self.get_credential(name)
        if not cred:
            raise ValueError(f"Credential '{name}' not found")

        provider_impl = get_provider(cred.provider)
        fields = provider_impl.get_env_var_fields()

        # For AWS, check ~/.aws/credentials file as fallback
        aws_file_creds = {}
        if cred.provider == "aws":
            aws_file_creds = _get_aws_credentials_from_file()

        values = {}
        missing = []

        for field in fields:
            env_var = f"{cred.env_var_prefix}_{field}"
            value = os.environ.get(env_var)

            if value:
                values[field] = value
            elif field in aws_file_creds:
                # Use AWS credentials file as fallback
                values[field] = aws_file_creds[field]
            elif field != "SESSION_TOKEN":  # SESSION_TOKEN is optional for AWS
                missing.append(env_var)

        if missing:
            if cred.provider == "aws":
                raise ValueError(
                    f"Missing environment variables: {', '.join(missing)}\n"
                    f"Also checked ~/.aws/credentials but credentials not found there.\n"
                    f"Set them with: export {missing[0]}='...'"
                )
            else:
                raise ValueError(
                    f"Missing environment variables: {', '.join(missing)}\n"
                    f"Set them with: export {missing[0]}='...'"
                )

        return values

    def test_credential(self, name: str) -> tuple[bool, str]:
        """Test credential by making API call.

        Args:
            name: Credential name

        Returns:
            Tuple of (success, message)

        Raises:
            ValueError: If credential not found
        """
        cred = self.get_credential(name)
        if not cred:
            raise ValueError(f"Credential '{name}' not found")

        # Load from environment
        try:
            values = self.get_credential_values(name)
        except ValueError as e:
            return False, str(e)

        # Test with provider
        provider_impl = get_provider(cred.provider)
        result = provider_impl.test_credentials(values)

        # Update database
        with get_db() as db:
            db_cred = db.query(CloudCredential).filter_by(name=name).first()
            db_cred.last_tested = datetime.utcnow()
            db_cred.test_status = "success" if result.success else "failed"
            db_cred.test_message = result.message
            db.commit()

        return result.success, result.message

    def update_last_used(self, name: str) -> None:
        """Update the last used timestamp for a credential.

        Args:
            name: Credential name
        """
        with get_db() as db:
            cred = db.query(CloudCredential).filter_by(name=name).first()
            if cred:
                cred.last_used = datetime.utcnow()
                db.commit()
