# 🚀 BYOVPN (Bring Your Own VPN)

Using a commercial VPN does not eliminate the man-in-the-middle; it simply shifts your threat model from your ISP to a third-party VPN company. You are forced to trust that they do not log your traffic or sell your data. 

BYOVPN is an Infrastructure-as-Code (IaC) tool designed to give you control over *how* you shift that threat model. By automating the deployment of an ephemeral WireGuard tunnel on your own cloud infrastructure, you own the keys, manage the server, and control the routing.

## 🚧 Current Status & Roadmap

Currently, BYOVPN uses Pulumi and Python to automatically provision infrastructure on **AWS EC2**. 

While AWS is highly reliable for on-demand use, it is not an anonymous provider. Our primary roadmap goal is to integrate support for various privacy-respecting VPS providers that do not keep logs. This will allow you to deploy secure tunnels on infrastructure tailored specifically for absolute privacy and heavy bandwidth usage.

## 🛠️ Prerequisites

* [uv](https://github.com/astral-sh/uv) installed
* [Pulumi CLI](https://www.pulumi.com/docs/install/) installed and authenticated
* Cloud credentials configured locally (e.g., `aws configure`)
* WireGuard tools (`wg`) installed locally for key generation

## ⚡ Quickstart

Navigate to the source directory and execute the main orchestration script to spin up your private tunnel.

```bash
cd src
uv run main.py --provider aws