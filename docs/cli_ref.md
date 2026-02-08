# CLI Command Reference

## Command Structure

```bash
vpn <command> <subcommand> [arguments] [options]
```

### Goals

* Commands named by what they do, not how they work
* Consistent: Similar patterns across all commands
* Safe: Destructive actions require confirmation (unless --force)
* Informative: Rich output
* Scriptable: All commands support --json output and --yes for automation

## Global Options

Available on all commands:
```bash
--help, -h              Show help message and exit
--verbose, -v           Increase output verbosity (can repeat: -vv, -vvv)
--quiet, -q             Suppress non-error output
--json                  Output in JSON format (for scripting)
--no-color              Disable colored output
--config <path>         Use alternative config file
--version               Show version and exit
```

## Authentication and Credentials

### `vpn auth add <provider>`

Add cloud provider API credentials.

**Arguments:**

- `<provider>` - Cloud provider name
  - Choices: `hetzner`, `digitalocean`, `aws`, `gcp`, `vultr`, `oracle`

**Options:**

- `--name <name>` - Friendly name for credential set (default: provider name)
- `--token <token>` - API token (if not provided, prompts securely)
- `--from-env` - Read token from environment variable
- `--test` - Test credentials immediately after adding

**Examples:**

```bash
# Interactive (recommended)
vpn auth add hetzner

# Prompts for token, provides instructions:
# Enter Hetzner API token: ****************************************
# 
# To get a token:
# 1. Visit https://console.hetzner.cloud
# 2. Select your project
# 3. Go to Security → API Tokens
# 4. Create token with Read & Write permissions
#
# Testing credentials...
#  Successfully authenticated as: user@example.com
#  Credentials saved securely

# Non-interactive
vpn auth add hetzner --token $HCLOUD_TOKEN --name production

# From environment variable
export HCLOUD_TOKEN=abc123...
vpn auth add hetzner --from-env

# AWS credentials
vpn auth add aws
# Prompts for:
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ********
```

**Where credentials are stored:**
- macOS: Keychain
- Linux: Secret Service (gnome-keyring, kwallet)
- Windows: Credential Manager

**Security notes:**
- Credentials encrypted at rest
- Never logged or displayed
- Never committed to git
- Can be rotated without recreating servers

---

### `vpn auth list`

List all saved cloud provider credentials.

**Options:**
- `--provider <provider>` - Filter by provider
- `--format <table|json|yaml>` - Output format (default: table)

**Examples:**

```bash
vpn auth list

# Output:
Saved Credentials:
┌─────────────┬──────────────┬─────────────────────┬──────────────┐
│ Name        │ Provider     │ Created             │ Last Used    │
├─────────────┼──────────────┼─────────────────────┼──────────────┤
│ production  │ hetzner      │ 2026-01-15 10:23    │ 2 hours ago  │
│ personal    │ digitalocean │ 2026-01-20 15:45    │ Never        │
│ aws-main    │ aws          │ 2026-02-01 09:15    │ 5 days ago   │
└─────────────┴──────────────┴─────────────────────┴──────────────┘

vpn auth list --provider hetzner --format json
# [{"name": "production", "provider": "hetzner", "created": "2026-01-15T10:23:00Z"}]
```

---

### `vpn auth remove <name>`

Remove stored credentials.

**Arguments:**
- `<name>` - Credential name or ID to remove

**Options:**
- `--force`, `-f` - Skip confirmation prompt

**Examples:**

```bash
vpn auth remove production

# Interactive confirmation:
# Warning: This will remove credentials "production"
# Any servers using these credentials will need to be managed manually.
# Continue? [y/N]: 

# Force without confirmation
vpn auth remove production --force
```

**Notes:**
- Removing credentials doesn't affect existing servers
- Servers can still be managed via Pulumi state
- Can't provision new servers without credentials

---

### `vpn auth test <name>`

Test if credentials are valid and have proper permissions.

**Arguments:**
- `<name>` - Credential name to test

**Examples:**

```bash
vpn auth test production

# Output:

# If valid: Give success message and important info

# If invalid: Give an error message
```

---

## Server Management

### `vpn create`

Create and provision a new VPN server.

**Options:**

**Provider Selection:**
- `--provider <name>` - Cloud provider (required if multiple credentials)
  - Choices: `hetzner`, `digitalocean`, `aws`
- `--credentials <name>` - Specific credential set to use

**Location:**
- `--region <region>` - Region/location code (default: auto-select closest)
- `--list-regions` - Show available regions and exit

**Server Size:**
- `--size <small|medium|large>` - Predefined server size (default: `small`)
- `--instance-type <type>` - Provider-specific instance type (overrides `--size`)

**Configuration:**
- `--config <file>` - YAML config file with server settings and apps
- `--name <name>` - Friendly server name (default: auto-generated)

**Connection:**
- `--connect` - Connect to VPN immediately after creation
- `--no-connect` - Don't auto-connect (default)

**Examples:**

```bash
# Minimal (interactive prompts)
vpn create
# Prompts for:
# - Provider (if multiple credentials)
# - Region
# - Size

# Non-interactive with defaults
vpn create --provider hetzner --region nbg1 --size small

# Create and connect immediately
vpn create --provider hetzner --region nbg1 --connect

# Specific instance type
vpn create --provider aws --instance-type t3.micro --region us-east-1

# With config file
vpn create --config production-server.yml

# Custom name
vpn create --provider hetzner --name "work-vpn"

# List available regions first
vpn create --provider hetzner --list-regions
# Available Regions:
# - nbg1: Nuremberg, Germany
# - fsn1: Falkenstein, Germany
# - hel1: Helsinki, Finland
# - ash:  Ashburn, Virginia, USA
# - hil:  Hillsboro, Oregon, USA
```

**Output:**

```bash
Creating VPN server...

[1/5] Stuff...
[2/5] Stuff...
[3/5] Stuff...
[4/5] Stuff...
[5/5] Stuff...

Server created successfully!

  ID:       vpn-nbg1-a4f2b8c9
  Name:     vpn-nbg1-a4f2b8c9
  Provider: Hetzner Cloud
  Region:   Nuremberg, Germany
  IP:       95.217.123.45
  Cost:     ~$4.10/month

Connect with: vpn connect vpn-nbg1-a4f2b8c9
```

---

### `vpn list`

List all VPN servers.

**Options:**
- `--provider <provider>` - Filter by cloud provider
- `--region <region>` - Filter by region
- `--status <status>` - Filter by status
  - Choices: `provisioning`, `ready`, `connected`, `stopped`, `error`
- `--sort <field>` - Sort by field (default: `created`)
  - Choices: `created`, `name`, `region`, `cost`, `status`
- `--format <table|json|yaml>` - Output format (default: table)

**Examples:**

```bash
# List all servers
vpn list

# Output:
VPN Servers:
┌────────────────┬──────────┬───────────┬────────────────┬──────────┬──────────┐
│ ID             │ Provider │ Region    │ IP             │ Status   │ Cost/mo  │
├────────────────┼──────────┼───────────┼────────────────┼──────────┼──────────┤
│ vpn-nbg1-a4f2  │ hetzner  │ nbg1      │ 95.217.123.45  │ ready    │ $4.10    │
│ vpn-nyc1-8f3d  │ do       │ nyc1      │ 134.122.45.67  │ connected│ $6.00    │
│ vpn-ash-1b2c   │ hetzner  │ ash       │ 148.251.78.90  │ ready    │ $4.10    │
└────────────────┴──────────┴───────────┴────────────────┴──────────┴──────────┘

Total: 3 servers ($14.20/month estimated)

# Filter by provider
vpn list --provider hetzner

# Filter by status
vpn list --status connected

# Sort by cost
vpn list --sort cost

# JSON output for scripting
vpn list --format json | jq -r '.[] | select(.status=="ready") | .id'
```

**Status meanings:**
- `provisioning` - Being created (pulumi running)
- `ready` - Running and available to connect
- `connected` - Currently connected to this server
- `stopped` - Server stopped but not destroyed
- `error` - Problem with server (check logs)

---

### `vpn info <server-id>`

Show detailed information about a server.

**Arguments:**
- `<server-id>` - Server ID to show (or use `--current`)

**Options:**
- `--current` - Show info for currently connected server
- `--format <table|json|yaml>` - Output format (default: table)

**Examples:**

```bash
vpn info vpn-nbg1-a4f2

# Output:
Server: vpn-nbg1-a4f2b8c9
---------------------------------------

Cloud Provider:    Hetzner Cloud
Region:            nbg1 (Nuremberg, Germany)
Instance Type:     CAX11 (2 vCPU ARM, 4GB RAM)
Instance ID:       12345678

Network:
  Public IPv4:     95.217.123.45
  Public IPv6:     2a01:4f8:1c1c:1234::1
  VPN Network:     10.0.0.0/24
  VPN IP:          10.0.0.1

WireGuard:
  Public Key:      abc123def456...xyz789
  Listen Port:     51820
  Active Peers:    1
  Last Handshake:  3 seconds ago

Status:            Ready
Uptime:            3d 14h 23m
Created:           2026-02-01 10:23:45 UTC
Last Connected:    2 hours ago

Installed Apps:    2
   pihole         (running) - http://10.0.0.1/admin
   wireguard-ui   (running) - http://10.0.0.1:8080

Cost Estimate:     $4.10/month
Bandwidth:         ↑ 145 MB  ↓ 2.3 GB

# Show currently connected server
vpn info --current

# JSON format
vpn info vpn-nbg1-a4f2 --format json
```

---

### `vpn destroy <server-id>`

Permanently delete a VPN server and all resources.

**Arguments:**
- `<server-id>` - Server ID to destroy

**Options:**
- `--force`, `-f` - Skip confirmation prompt
- `--keep-pulumi` - Don't delete pulumi state files
- `--disconnect` - Disconnect first if connected (default: true)

**Examples:**

```bash
# Interactive (prompts for confirmation)
vpn destroy vpn-nbg1-a4f2

# Output:
Warning: This will permanently delete server vpn-nbg1-a4f2b8c9

The following will be destroyed:
  - Cloud server (95.217.123.45)
  - All installed apps and data
  - Pulumi state
  - WireGuard configuration

Estimated cost saved: $4.10/month

This action cannot be undone. Continue? [y/N]: y

Destroying server...
 Disconnecting VPN... (if connected)
 Running pulumi destroy... (30s)
 Cleaning up local state...
 Removing configuration files...

Server vpn-nbg1-a4f2b8c9 destroyed successfully.

# Force without confirmation
vpn destroy vpn-nbg1-a4f2 --force

# Keep pulumi state (for debugging)
vpn destroy vpn-nbg1-a4f2 --keep-pulumi
```

**What gets deleted:**
- Cloud resources (server, firewall, SSH keys)
- Local WireGuard config
- Local SSH keys
- Pulumi state
- Database records
- Connection history

**What's NOT deleted:**
- Credentials (reusable for new servers)
- App catalog
- User preferences
- Activity logs

---

### `vpn start <server-id>`

Start a stopped server. (Later on feature)

**Arguments:**
- `<server-id>` - Server ID to start

**Examples:**

```bash
vpn start vpn-nbg1-a4f2

# Output:
Starting server vpn-nbg1-a4f2b8c9...
 Server started
 Waiting for boot... (60s)
 Server ready

Connect with: vpn connect vpn-nbg1-a4f2
```

**Note:** Not all cloud providers support stopping/starting servers. Some require full recreation.

---

### `vpn stop <server-id>`

Stop a running server without destroying. (Later on feature)

**Arguments:**
- `<server-id>` - Server ID to stop

**Options:**
- `--disconnect` - Disconnect VPN first (default: true)

**Examples:**

```bash
vpn stop vpn-nbg1-a4f2

# Output:
Stopping server vpn-nbg1-a4f2b8c9...
 Disconnecting VPN...
 Server stopped

Note: You will still be charged for storage.
      To completely remove server, use: vpn destroy vpn-nbg1-a4f2
```

---

## Connection Management

### `vpn connect [server-id]`

Connect to a VPN server.

**Arguments:**
- `[server-id]` - Server to connect to (optional)

**Options:**
- `--kill-switch` - Enable kill switch (blocks non-VPN traffic) [Phase 3]
- `--dns <servers>` - Override DNS servers (comma-separated IPs)
- `--split-tunnel <cidrs>` - Only route specific networks through VPN [Phase 3]

**Examples:**

```bash
# Connect to specific server
vpn connect vpn-nbg1-a4f2

# Output:
Connecting to vpn-nbg1-a4f2b8c9 (Nuremberg, DE)...

 Validating server status...
 Loading WireGuard configuration...
 Applying routing rules...
 Starting WireGuard interface...
 Establishing handshake...
 Verifying connection...

Connected successfully!

  Your IP:    95.217.123.45
  Latency:    45ms
  DNS:        10.0.0.1 (Pi-hole)
  
All traffic is now routed through the VPN.

# Auto-select (uses last connected or prompts)
vpn connect

# If no history:
Select server to connect to:
  1. vpn-nbg1-a4f2 (Nuremberg, DE) - Created 2d ago
  2. vpn-nyc1-8f3d (New York, US) - Created 5d ago
Choice [1]: 

# With custom DNS
vpn connect vpn-nbg1-a4f2 --dns 1.1.1.1,8.8.8.8

# With kill switch (Phase 3)
vpn connect vpn-nbg1-a4f2 --kill-switch
```

**Requirements:**
- `wg-quick` must be installed
- `sudo` access (for network configuration)
- Server must be in "ready" state

---

### `vpn disconnect`

Disconnect from the current VPN.

**Options:**
- `--force`, `-f` - Force disconnect even if errors occur

**Examples:**

```bash
vpn disconnect

# Output:
Disconnecting VPN...
 Stopping WireGuard interface...
 Restoring system routing...
 Restoring DNS configuration...

Disconnected successfully.

Session Summary:
  Duration:         3h 24m
  Data transferred: ↑ 145 MB  ↓ 2.3 GB
  Server:           vpn-nbg1-a4f2 (Nuremberg, DE)

# Force (if cleanup fails)
vpn disconnect --force
```

**Note:** Does not destroy the server, only disconnects.

---

### `vpn status`

Show current VPN connection status.

**Options:**
- `--json` - Output JSON format
- `--monitor` - Continuous monitoring mode (updates every 5s)
- `--verbose`, `-v` - Show detailed network information

**Examples:**

```bash
# Basic status
vpn status

# When connected:
Connected to vpn-nbg1-a4f2b8c9
  Server:         Nuremberg, Germany
  Your IP:        95.217.123.45
  Latency:        45ms
  Uptime:         3h 24m
  
  Traffic:        ↑ 145 MB  ↓ 2.3 GB
  DNS:            10.0.0.1 (via Pi-hole)
  
  Last handshake: 3 seconds ago
  Interface:      wg0 (UP)

# When disconnected:
Not connected

Your IP:        73.12.45.67
ISP:            Verizon

Available servers:
  - vpn-nbg1-a4f2 (Nuremberg, DE) - Last used 2h ago
  - vpn-nyc1-8f3d (New York, US) - Never used

Connect with: vpn connect <server-id>

# Verbose output
vpn status -v

# Shows additional info:
#   WireGuard Interface Details
#   Routing Table
#   DNS Configuration
#   Network Diagnostics

# Continuous monitoring
vpn status --monitor
# Updates every 5 seconds, Ctrl+C to stop

# JSON for scripting
vpn status --json
{
  "connected": true,
  "server_id": "vpn-nbg1-a4f2",
  "server_region": "nbg1",
  "public_ip": "95.217.123.45",
  "latency_ms": 45,
  "uptime_seconds": 12240,
  "bytes_sent": 152043520,
  "bytes_received": 2469606400
}
```

**Monitoring mode:**
```bash
vpn status --monitor

# Real-time updating display:
  Connected to vpn-nbg1-a4f2b8c9
  Latency: 45ms (↓ from 48ms)
  Traffic: ↑ 145.2 MB (+0.5 MB/s)  ↓ 2.3 GB (+1.2 MB/s)
  Handshake: 2s ago
  
Press Ctrl+C to exit
```

---

### `vpn reconnect`

Disconnect and reconnect to VPN.

**Options:**
- `--server <server-id>` - Reconnect to different server

**Examples:**

```bash
# Reconnect to current server
vpn reconnect

# Output:
Reconnecting...
 Disconnected
 Connected to vpn-nbg1-a4f2

# Switch to different server
vpn reconnect --server vpn-nyc1-8f3d

# Output:
Reconnecting to vpn-nyc1-8f3d...
 Disconnected from vpn-nbg1-a4f2
 Connected to vpn-nyc1-8f3d
```

**Use cases:**
- After app installation (to apply new DNS settings)
- After network change (switching WiFi)
- To refresh connection
- To switch servers quickly

---

## App Store

### `vpn apps list`

List available apps from the catalog.

**Options:**
- `--category <category>` - Filter by category
  - Choices: `privacy`, `dns`, `proxy`, `storage`, `management`, `monitoring`
- `--search <query>` - Search app names and descriptions
- `--format <table|json|yaml>` - Output format
- `--installed` - Show only installed apps (shortcut for `vpn apps installed`)

**Examples:**

```bash
# List all apps
vpn apps list

# Output:
Available Apps:
┌──────────────────┬───────────┬─────────────────────────────────────┬────────────┐
│ ID               │ Category  │ Description                         │ Resources  │
├──────────────────┼───────────┼─────────────────────────────────────┼────────────┤
│ pihole           │ privacy   │ Network-wide ad blocking            │ 512MB RAM  │
│ wireguard-ui     │ mgmt      │ Web interface for WireGuard         │ 256MB RAM  │
│ dns-over-https   │ privacy   │ Encrypted DNS queries               │ 256MB RAM  │
│ tor-bridge       │ privacy   │ Tor bridge relay                    │ 512MB RAM  │
│ nextcloud        │ storage   │ Personal cloud storage              │ 2GB RAM    │
│ syncthing        │ storage   │ Peer-to-peer file sync              │ 512MB RAM  │
│ shadowsocks      │ proxy     │ SOCKS5 proxy server                 │ 256MB RAM  │
└──────────────────┴───────────┴─────────────────────────────────────┴────────────┘

7 apps available
Use 'vpn apps info <app-id>' for details

# Filter by category
vpn apps list --category privacy

Privacy Apps:
  - pihole - Network-wide ad blocking
  - dns-over-https - Encrypted DNS queries  
  - tor-bridge - Tor bridge relay

# Search
vpn apps list --search "dns"

Apps matching "dns":
  - pihole - Network-wide ad blocking (includes DNS)
  - dns-over-https - Encrypted DNS queries

# Show installed apps only
vpn apps list --installed
```

---

### `vpn apps info <app-id>`

Show detailed information about an app.

**Arguments:**
- `<app-id>` - App identifier

**Options:**
- `--format <text|json|yaml>` - Output format

**Examples:**

```bash
vpn apps info pihole

# Output:
┌─────────────────────────────────────────────────────────────────┐
│ Pi-hole - Network-wide ad blocking                              │
├─────────────────────────────────────────────────────────────────┤
│ Category:    privacy                                            │
│ Version:     2024.01                                            │
│ Resources:   512MB RAM, 1GB disk                                │
│ Ports:       80/tcp (web), 53/udp (DNS)                         │
│ Author:      Pi-hole Team                                       │
│ License:     EUPL-1.2                                           │
└─────────────────────────────────────────────────────────────────┘

Description:
  Pi-hole is a DNS sinkhole that blocks ads and trackers at the 
  network level. Once installed, all devices connected to your VPN
  will have ad-blocking automatically.

Features:
  - Network-wide ad blocking (no per-device config needed)
  - Web-based dashboard with statistics
  - Customizable blocklists
  - Query logging and analysis
  - Whitelist/blacklist management

Configuration Options:
  web_password (required, secret)
    Admin interface password
    
  upstream_dns (optional, default: [1.1.1.1, 8.8.8.8])
    DNS servers to forward queries to
    
  blocklists (optional)
    Ad blocklists to use
    
  dns_over_https (optional, default: false)
    Enable DNS-over-HTTPS upstream

Post-Install:
  Web Interface:  http://10.0.0.1/admin
  Access:         Only from VPN network (10.0.0.0/24)
  DNS:            Automatically configured for VPN clients

Install:
  vpn apps install pihole
  vpn apps install pihole --config pihole-config.yml

Documentation:
  https://docs.pi-hole.net/
```

---

### `vpn apps install <app-id>`

Install an app on your VPN server.

**Arguments:**
- `<app-id>` - App to install

**Options:**

**Server Selection:**
- `--server <server-id>` - Install on specific server (default: currently connected)

**Configuration:**
- `--config <file>` - YAML configuration file
- `--set <key=value>` - Set config value (can be repeated)
- `--yes`, `-y` - Use default values for all prompts

**Behavior:**
- `--skip-health-check` - Don't verify app started correctly
- `--no-reconnect` - Don't reconnect VPN after installation

**Examples:**

```bash
# Interactive installation (prompts for config)
vpn apps install pihole

# Output:
Installing Pi-hole on vpn-nbg1-a4f2b8c9...

Configuration:
  Web admin password: ********
  Upstream DNS servers [1.1.1.1, 8.8.8.8]: 
  Enable DNS-over-HTTPS? [y/N]: y
  
 Validating configuration...
 Checking server resources... (512MB required, 3.2GB available)
 Deploying Nix configuration...
 Uploading to server...
 Rebuilding NixOS... (45s)
 Starting Pi-hole service...
 Health check passed

Pi-hole installed successfully!

 Web Interface: http://10.0.0.1/admin
 Password: [saved to keyring]

To use Pi-hole's ad blocking:
  1. Reconnect to VPN: vpn reconnect
  2. DNS will automatically use Pi-hole
  3. Visit http://pi.hole/admin to view stats

# Non-interactive with config file
vpn apps install pihole --config pihole.yml --yes

# pihole.yml:
# web_password: "my-secure-password"
# upstream_dns:
#   - "1.1.1.1"
#   - "8.8.8.8"
# dns_over_https: true

# Non-interactive with CLI flags
vpn apps install pihole \
  --set web_password=secret \
  --set upstream_dns=1.1.1.1,8.8.8.8 \
  --set dns_over_https=true \
  --yes

# Install on specific server
vpn apps install pihole --server vpn-nyc1-8f3d

# Install without reconnecting (advanced)
vpn apps install pihole --no-reconnect
```

---

### `vpn apps installed [server-id]`

List installed apps.

**Arguments:**
- `[server-id]` - Show apps on specific server (default: all servers)

**Options:**
- `--current` - Show only apps on currently connected server
- `--format <table|json|yaml>` - Output format

**Examples:**

```bash
# List all installed apps (all servers)
vpn apps installed

# Output:
Installed Apps:

Server: vpn-nbg1-a4f2b8c9 (Nuremberg, DE)
┌──────────────────┬───────────┬─────────────────────────────────┐
│ App              │ Status    │ Access                          │
├──────────────────┼───────────┼─────────────────────────────────┤
│ pihole           │  running │ http://10.0.0.1/admin            │
│ wireguard-ui     │  running │ http://10.0.0.1:8080             │
└──────────────────┴───────────┴─────────────────────────────────┘

Server: vpn-nyc1-8f3d (New York, US)
┌──────────────────┬───────────┬─────────────────────────────────┐
│ App              │ Status    │ Access                          │
├──────────────────┼───────────┼─────────────────────────────────┤
│ nextcloud        │  running  │ https://cloud.example.com       │
│ syncthing        │   stopped │ -                               │
└──────────────────┴───────────┴─────────────────────────────────┘

Total: 4 apps across 2 servers
Resource usage: 2.7GB / 6GB RAM

# Apps on specific server
vpn apps installed vpn-nbg1-a4f2

# Apps on currently connected server
vpn apps installed --current

# JSON format
vpn apps installed --format json
```

---

### `vpn apps uninstall <app-id>`

Remove an installed app.

**Arguments:**
- `<app-id>` - App to uninstall

**Options:**
- `--server <server-id>` - Uninstall from specific server (default: current)
- `--purge` - Remove all app data and configuration
- `--force`, `-f` - Skip confirmation
- `--no-reconnect` - Don't reconnect VPN after uninstallation

**Examples:**

```bash
# Interactive (prompts for confirmation)
vpn apps uninstall pihole

# Output:
Warning: This will remove Pi-hole from vpn-nbg1-a4f2b8c9

The following will be removed:
  - Pi-hole service
  - Web interface
  - DNS blocking functionality
  - App configuration

Continue? [y/N]: y

Uninstalling Pi-hole...
 Stopping Pi-hole service...
 Removing configuration...
 Rebuilding NixOS... (30s)
 Uninstalled successfully

Note: Reconnect to VPN to use default DNS servers
      vpn reconnect

# Force without confirmation
vpn apps uninstall pihole --force

# Purge all data
vpn apps uninstall nextcloud --purge
# Removes app AND all stored data (files, databases, etc.)

# Uninstall from specific server
vpn apps uninstall pihole --server vpn-nyc1-8f3d
```

---

### `vpn apps upgrade <app-id>`

Upgrade an app to latest version. (Phase 3 feature)

**Arguments:**
- `<app-id>` - App to upgrade

**Options:**
- `--server <server-id>` - Upgrade on specific server
- `--version <version>` - Upgrade to specific version (default: latest)

---

### `vpn apps logs <app-id>`

View app logs.

**Arguments:**
- `<app-id>` - App to view logs for

**Options:**
- `--server <server-id>` - View logs from specific server (default: current)
- `--follow`, `-f` - Follow logs in real-time
- `--lines <n>`, `-n <n>` - Number of lines to show (default: 50)
- `--since <time>` - Show logs since time (e.g., "1h", "2023-01-01")
- `--level <level>` - Filter by log level
  - Choices: `debug`, `info`, `warning`, `error`

**Examples:**

```bash
# Show last 50 lines
vpn apps logs pihole

# Output:
[2026-02-07 10:23:45] INFO: Pi-hole FTL v5.21 started
[2026-02-07 10:23:46] INFO: Loading blocklists...
[2026-02-07 10:23:50] INFO: Loaded 1,234,567 domains
[2026-02-07 10:24:01] INFO: DNS query: google.com -> allowed
[2026-02-07 10:24:15] INFO: DNS query: ads.tracker.com -> blocked
[2026-02-07 10:24:23] INFO: DNS query: youtube.com -> allowed
[2026-02-07 10:25:12] INFO: DNS query: doubleclick.net -> blocked

# Follow logs in real-time
vpn apps logs pihole --follow
# Shows logs continuously, Ctrl+C to exit

# Show last 100 lines
vpn apps logs pihole --lines 100

# Show errors only
vpn apps logs pihole --level error

# Show logs from last hour
vpn apps logs pihole --since 1h

# Show logs from specific date
vpn apps logs pihole --since 2026-02-01
```

---

### `vpn apps status <app-id>`

Check app health and status.

**Arguments:**
- `<app-id>` - App to check

**Options:**
- `--server <server-id>` - Check on specific server (default: current)

**Examples:**

```bash
vpn apps status pihole

# Output:
Pi-hole Status on vpn-nbg1-a4f2b8c9:
------------------------------------

  Status:          Running
  Health:          Healthy
  Uptime:         3d 14h 23m
  Last check:     5 seconds ago
  
  Service Status:
     DNS server responding (port 53)
     Web interface accessible (port 80)
     Blocklists up to date
     Database operational
    
  Statistics (last 24 hours):
    Queries:      45,234
    Blocked:      12,567 (27.8%)
    Clients:      1
    
  Resources:
    Memory:       187MB / 512MB allocated
    Disk:         234MB / 1GB allocated

# If app has issues:
vpn apps status nextcloud

Nextcloud Status on vpn-nbg1-a4f2b8c9:
------------------------------------

  Status:         ✗ Error
  Health:         ✗ Unhealthy
  Last check:     2 minutes ago
  
  Issues:
    ✗ Database connection failed
    ✗ Cannot write to data directory
    
  Suggested Actions:
    1. Check logs: vpn apps logs nextcloud
    2. Verify disk space: vpn info vpn-nbg1-a4f2
    3. Restart app: vpn apps restart nextcloud
```

---

### `vpn apps config <app-id>`

Show current app configuration.

**Arguments:**
- `<app-id>` - App to show config for

**Options:**
- `--server <server-id>` - Show config from specific server (default: current)
- `--format <yaml|json>` - Output format
- `--reveal-secrets` - Show secret values (normally hidden with ******)

**Examples:**

```bash
# Show config (secrets hidden)
vpn apps config pihole

# Output:
Pi-hole Configuration:
  web_password:    ******** (secret)
  upstream_dns:
    - 1.1.1.1
    - 8.8.8.8
  blocklists:
    - https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
  dns_over_https:  true
  ipv6_support:    true

# Reveal secrets (use with caution)
vpn apps config pihole --reveal-secrets

# Output:
Pi-hole Configuration:
  web_password:    my-secret-password-123
  upstream_dns:
    - 1.1.1.1
    - 8.8.8.8
  ...

# JSON format
vpn apps config pihole --format json
```

---

### `vpn apps export <app-id>`

Export app configuration to file.

**Arguments:**
- `<app-id>` - App to export

**Options:**
- `--server <server-id>` - Export from specific server
- `--output <file>` - Output file (default: stdout)
- `--format <yaml|json>` - Output format
- `--include-secrets` - Include secret values in export

**Examples:**

```bash
# Export to stdout
vpn apps export pihole

# Export to file
vpn apps export pihole --output pihole-backup.yml

# Export with secrets (for backup)
vpn apps export pihole --output pihole-backup.yml --include-secrets

# Later, restore with:
vpn apps install pihole --config pihole-backup.yml

# Export all apps from a server
for app in $(vpn apps installed --current --format json | jq -r '.[].app_id'); do
  vpn apps export $app --output "${app}-config.yml"
done
```

---

### `vpn apps import <config-file>`

Import and install app from config file.

**Arguments:**
- `<config-file>` - Configuration file to import

**Options:**
- `--server <server-id>` - Install on specific server

**Examples:**

```bash
# Import config
vpn apps import pihole-config.yml

# Reads config file and installs app with saved settings
```

---

## Configuration

### `vpn config get <key>`

Get configuration value.

**Arguments:**
- `<key>` - Configuration key (dot notation for nested values)

**Examples:**

```bash
# Get single value
vpn config get defaults.provider
# hetzner

vpn config get connection.dns
# 10.0.0.1

vpn config get display.color
# true
```

---

### `vpn config set <key> <value>`

Set configuration value.

**Arguments:**
- `<key>` - Configuration key
- `<value>` - New value

**Examples:**

```bash
# Set default provider
vpn config set defaults.provider hetzner

# Set default region
vpn config set defaults.region nbg1

# Set auto-connect preference
vpn config set defaults.auto_connect true

# Enable kill switch by default (Phase 3)
vpn config set connection.kill_switch true

# Custom DNS servers
vpn config set connection.dns "1.1.1.1,8.8.8.8"

# Disable colors
vpn config set display.color false

# Set log level
vpn config set advanced.log_level debug
```

**Common settings:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `defaults.provider` | string | (none) | Default cloud provider |
| `defaults.region` | string | (none) | Default region |
| `defaults.size` | string | small | Default server size |
| `defaults.auto_connect` | bool | false | Auto-connect after create |
| `connection.kill_switch` | bool | false | Enable kill switch |
| `connection.dns` | string | auto | DNS servers |
| `connection.ipv6` | bool | true | Enable IPv6 |
| `connection.persistent_keepalive` | int | 25 | WireGuard keepalive |
| `display.color` | bool | true | Use colors |
| `display.verbose` | bool | false | Verbose output |
| `advanced.log_level` | string | info | Log level |

---

### `vpn config list`

List all configuration settings.

**Options:**
- `--format <table|yaml|json>` - Output format
- `--defaults` - Show only non-default values

**Examples:**

```bash
# Show all settings
vpn config list

# Output:
Configuration:
------------------------------------

Defaults:
  provider:       hetzner
  region:         nbg1
  size:           small
  auto_connect:   false

Connection:
  kill_switch:    false
  dns:            auto
  ipv6:           true

Display:
  color:          true
  verbose:        false

Advanced:
  log_level:      info

# Show only non-default values
vpn config list --defaults

# YAML format
vpn config list --format yaml
```

---

### `vpn config reset`

Reset configuration to defaults.

**Options:**
- `--force`, `-f` - Skip confirmation

**Examples:**

```bash
# Interactive
vpn config reset

# Output:
Warning: This will reset all configuration to defaults.
Continue? [y/N]: y

 Configuration reset to defaults

# Force
vpn config reset --force
```

---

### `vpn config edit`

Open config file in text editor. (Phase 3 feature)

**Uses `$EDITOR` environment variable**

**Examples:**

```bash
# Edit config file
vpn config edit

# Opens ~/.config/vpn/config.yml in your editor
# (vim, nano, code, etc.)
```

---

## Utilities & Diagnostics

### `vpn doctor`

Diagnose system and check requirements.

**Options:**
- `--fix` - Attempt to auto-fix issues
- `--verbose`, `-v` - Show detailed checks

**Examples:**

```bash
vpn doctor

# Output:
System Diagnostics
------------------------------------━━━━

Dependencies:
   WireGuard tools installed (wg 1.0.20210914)
   pulumi available (v1.7.0)
   SSH available (OpenSSH_9.3)
   Python 3.11.7

Configuration:
   Config file exists (~/.config/vpn/config.yml)
   Database initialized (3 tables)
   Credentials stored: 2 providers

Network:
   Internet connectivity (ping 1.1.1.1)
   DNS resolution working
   Can reach cloud APIs:
     Hetzner API
     DigitalOcean API

Servers:
   2 servers configured
   1 server connected (vpn-nbg1-a4f2)
   1 server unhealthy (vpn-nyc1-8f3d)
    Server not responding to ping
    Last seen: 2 days ago
    Suggestion: Check server status in cloud console
                or run: vpn destroy vpn-nyc1-8f3d

Apps:
   3 apps installed
   All apps healthy

System:
   Disk space: 45GB available
   Memory: 8GB available
   OS: Linux 6.1.0-x86_64
  
Overall: 1 issue found

Run with --fix to attempt automatic repairs

# Attempt auto-fix
vpn doctor --fix

# Tries to fix issues automatically:
# - Reinstall missing dependencies
# - Repair database
# - Reset network configuration
# - etc.

# Verbose output
vpn doctor -v
# Shows detailed checks and results
```

---

### `vpn logs`

View activity logs.

**Options:**
- `--level <level>` - Filter by log level
  - Choices: `debug`, `info`, `warning`, `error`
- `--component <component>` - Filter by component
  - Choices: `pulumi`, `wireguard`, `ssh`, `apps`, `database`, `api`
- `--lines <n>`, `-n <n>` - Number of lines (default: 50)
- `--follow`, `-f` - Follow logs in real-time
- `--since <time>` - Show logs since time

**Examples:**

```bash
# Show last 50 lines
vpn logs

# Output:
[2026-02-07 10:15:23] INFO  [cli] Command: vpn create --provider hetzner
[2026-02-07 10:15:24] INFO  [wireguard] Generated keypair
[2026-02-07 10:15:25] INFO  [pulumi] Initializing pulumi
[2026-02-07 10:15:30] INFO  [pulumi] Applying configuration
[2026-02-07 10:17:12] INFO  [pulumi] Server created: 95.217.123.45
[2026-02-07 10:17:45] INFO  [ssh] Connected to server
[2026-02-07 10:17:50] INFO  [wireguard] Retrieved server public key

# Show errors only
vpn logs --level error

# Show errors from last hour
vpn logs --level error --since 1h

# Filter by component
vpn logs --component pulumi

# Follow logs
vpn logs --follow

# Show last 100 lines
vpn logs --lines 100
```

---

### `vpn costs`

Show cost estimates and usage.

**Options:**
- `--month <YYYY-MM>` - Show specific month (default: current)
- `--breakdown` - Show per-server breakdown
- `--format <table|json>` - Output format

**Examples:**

```bash
# Current month costs
vpn costs

# Output:
Cost Estimate - February 2026
------------------------------------

Servers:
  vpn-nbg1-a4f2   Hetzner CAX11     $4.10/month  (28 days active)
  vpn-nyc1-8f3d   DO Basic          $6.00/month  (15 days active)

Bandwidth:
  Total egress:   45.2 GB
  Cost:           $0.00 (within included limits)

Total Estimate:  $10.10 for February
Daily average:   $0.36/day
Year to date:    $48.50

Note: Estimates based on:
  - Current server uptime
  - Provider pricing
  - Bandwidth usage

Actual costs may vary. Check provider billing for exact amounts.

Last updated: 2 minutes ago

# Specific month
vpn costs --month 2026-01

# Detailed breakdown
vpn costs --breakdown

# Shows per-day costs, bandwidth per server, etc.

# JSON output
vpn costs --format json
```

---

### `vpn version`

Show version and system information.

**Options:**
- `--check-update` - Check for newer version

**Examples:**

```bash
vpn version

# Output:
vpn 0.1.0

Build Information:
  Python:        3.11.7
  uv:            0.1.16
  Platform:      Linux-6.1.0-x86_64-with-glibc2.35
  
Configuration:
  Config dir:    ~/.config/vpn
  Data dir:      ~/.local/share/vpn
  Cache dir:     ~/.cache/vpn

Dependencies:
  WireGuard:     1.0.20210914
  pulumi:        1.7.0 (bundled)
  SSH:           OpenSSH_9.3
  
Project:
  Homepage:      https://github.com/you/personal-vpn
  Documentation: https://docs.personal-vpn.dev
  Issues:        https://github.com/you/personal-vpn/issues

# Check for updates
vpn version --check-update

# Output:
Current version:  0.1.0
Latest version:   0.2.0

A new version is available!

What's new in 0.2.0:
  - Added multi-region failover
  - Improved connection stability
  - New apps: Jellyfin, Home Assistant
  - Bug fixes and performance improvements

Update with:
  uv tool upgrade personal-vpn

Changelog:
  https://github.com/byovpn/releases/tag/v0.2.0
```

---

### `vpn completion <shell>`

Generate shell completion script. (Phase 3 feature)

**Arguments:**
- `<shell>` - Shell type
  - Choices: `bash`, `zsh`, `fish`, `powershell`

**Examples:**

```bash
# Bash
vpn completion bash > ~/.local/share/bash-completion/completions/vpn
source ~/.bashrc

# Zsh
vpn completion zsh > ~/.zfunc/_vpn
# Add to ~/.zshrc: fpath=(~/.zfunc $fpath)

# Fish
vpn completion fish > ~/.config/fish/completions/vpn.fish
```

---

## Advanced Commands

### `vpn tunnel` (Phase 3+)

Create SSH tunnel through VPN.

**Options:**
- `--local-port <port>` - Local port to bind
- `--remote-host <host>` - Remote host to connect to
- `--remote-port <port>` - Remote port

**Examples:**

```bash
# Forward local port 8080 to remote MySQL
vpn tunnel --local-port 8080 --remote-host db.internal --remote-port 3306

# Access at: mysql -h 127.0.0.1 -P 8080
```

---

### `vpn benchmark` (Phase 3+)

Benchmark VPN performance.

**Examples:**

```bash
vpn benchmark

# Output:
Benchmarking vpn-nbg1-a4f2b8c9...

Download speed:    95.3 Mbps
Upload speed:      45.2 Mbps
Latency:           45ms (avg)
Jitter:            3ms
Packet loss:       0.1%

Compared to direct connection:
  Download:  -12% (was 108 Mbps)
  Upload:    -8%  (was 49 Mbps)
  Latency:   +40ms (was 5ms)
```

---

### `vpn migrate <old-server> <new-server>` (Phase 3+)

Migrate apps from one server to another.

**Arguments:**
- `<old-server>` - Source server ID
- `<new-server>` - Destination server ID

---

### `vpn backup` (Phase 3+)

Backup all configurations and state.

**Examples:**

```bash
vpn backup --output vpn-backup.tar.gz

# Creates archive with:
# - All server configurations
# - Installed app configs
# - Connection history
# - Preferences
```

---

### `vpn restore <backup-file>` (Phase 3+)

Restore from backup.

---