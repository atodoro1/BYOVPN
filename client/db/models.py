"""SQLAlchemy database models for BYOVPN.

Database schema with 5 tables:
1. cloud_credentials - Cloud provider API credential metadata
2. servers - VPN server inventory
3. wireguard_configs - Client-side WireGuard configurations
4. installed_apps - App installation history
5. connection_history - VPN connection session tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class CloudCredential(Base):
    """Table 1: Cloud provider credential metadata.

    Stores metadata about cloud provider credentials.
    Actual credentials are stored in environment variables.
    """
    __tablename__ = "cloud_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    env_var_prefix = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    last_tested = Column(DateTime, nullable=True)
    test_status = Column(String, nullable=True)
    test_message = Column(String, nullable=True)

    # Relationships
    servers = relationship("Server", back_populates="credential")


class Server(Base):
    """Table 2: VPN server inventory.

    Tracks all created VPN servers and their configuration.
    """
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    # Cloud provider info
    provider = Column(String, nullable=False)
    region = Column(String, nullable=False)
    instance_type = Column(String, nullable=False)
    instance_id = Column(String, nullable=True)
    credential_id = Column(Integer, ForeignKey("cloud_credentials.id"))

    # Network info
    public_ipv4 = Column(String, nullable=True)
    public_ipv6 = Column(String, nullable=True)
    vpn_network = Column(String, nullable=True)
    vpn_server_ip = Column(String, nullable=True)

    # WireGuard info
    wireguard_public_key = Column(String, nullable=True)
    wireguard_listen_port = Column(Integer, default=51820)

    # Status
    status = Column(String, nullable=False)

    # Cost tracking
    monthly_cost_estimate = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_connected = Column(DateTime, nullable=True)
    destroyed_at = Column(DateTime, nullable=True)

    # Pulumi state
    pulumi_stack_name = Column(String, nullable=True)
    pulumi_state_path = Column(String, nullable=True)

    # Relationships
    credential = relationship("CloudCredential", back_populates="servers")
    wireguard_config = relationship("WireGuardConfig", back_populates="server", uselist=False)
    installed_apps = relationship("InstalledApp", back_populates="server")
    connection_history = relationship("ConnectionHistory", back_populates="server")


class WireGuardConfig(Base):
    """Table 3: Client-side WireGuard configurations.

    Stores WireGuard configuration for connecting to servers.
    """
    __tablename__ = "wireguard_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.id"), unique=True, nullable=False)

    # Client keys
    client_private_key = Column(String, nullable=False)
    client_public_key = Column(String, nullable=False)
    client_preshared_key = Column(String, nullable=True)

    # Client IP
    client_ip = Column(String, nullable=False)

    # Server connection info
    server_endpoint = Column(String, nullable=False)
    server_public_key = Column(String, nullable=False)

    # DNS settings
    dns_servers = Column(String, nullable=True)

    # Routing
    allowed_ips = Column(String, nullable=False, default="0.0.0.0/0, ::/0")
    persistent_keepalive = Column(Integer, nullable=True, default=25)

    # Config file location
    config_file_path = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    server = relationship("Server", back_populates="wireguard_config")


class InstalledApp(Base):
    """Table 4: App installation history.

    Tracks which apps are installed on which servers.
    """
    __tablename__ = "installed_apps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False, index=True)

    # App identification
    app_id = Column(String, nullable=False, index=True)
    app_name = Column(String, nullable=False)
    app_version = Column(String, nullable=True)
    category = Column(String, nullable=True)

    # Installation details
    installed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    uninstalled_at = Column(DateTime, nullable=True)

    # Configuration
    config_snapshot = Column(Text, nullable=True)

    # Access info
    access_url = Column(String, nullable=True)
    access_port = Column(Integer, nullable=True)

    # Status
    status = Column(String, nullable=False, default="installing")
    health_status = Column(String, nullable=True)
    last_health_check = Column(DateTime, nullable=True)

    # Resource usage
    memory_allocated_mb = Column(Integer, nullable=True)
    disk_allocated_mb = Column(Integer, nullable=True)

    # Relationships
    server = relationship("Server", back_populates="installed_apps")


class ConnectionHistory(Base):
    """Table 5: VPN connection session tracking.

    Records each VPN connection session for usage tracking.
    """
    __tablename__ = "connection_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False, index=True)

    # Session timing
    connected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    disconnected_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Data transfer
    bytes_sent = Column(Integer, nullable=True)
    bytes_received = Column(Integer, nullable=True)

    # Connection quality
    avg_latency_ms = Column(Integer, nullable=True)
    max_latency_ms = Column(Integer, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)

    # Client info
    client_os = Column(String, nullable=True)
    client_hostname = Column(String, nullable=True)

    # Disconnect reason
    disconnect_reason = Column(String, nullable=True)

    # Relationships
    server = relationship("Server", back_populates="connection_history")
