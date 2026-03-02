# 🚀 BYOVPN (Build Your Own VPN)

**Own your VPN. Choose who has access to your data. Pay exactly as you go.**

Say goodbye to flat-rate monthly subscriptions and trusting third-party commercial VPN providers with your personal web traffic! BYOVPN is a powerful Infrastructure-as-Code (IaC) tool that automates the deployment of a highly secure, ephemeral WireGuard tunnel right on your own cloud infrastructure in minutes. 

## ✨ Why BYOVPN?
* **Absolute Privacy:** You hold the keys, manage the server, and control the routing. Zero third-party logging!
* **Pay-As-You-Go:** Only pay for the compute and bandwidth you actually use while your instance is running. 
* **Automated Provisioning:** Powered by Pulumi and Python, it seamlessly handles the cloud infrastructure and configures the WireGuard system automatically (currently defaulting to Debian environments).
* **Dynamic Client Configs:** Your local WireGuard client configuration file is generated and ready to use the second the server comes online!

## 🛠️ Prerequisites
* [uv](https://github.com/astral-sh/uv) installed
* [Pulumi CLI](https://www.pulumi.com/docs/install/) installed and authenticated
* Cloud credentials configured locally (e.g., `aws configure`)
* WireGuard tools (`wg`) installed locally for key generation

## ⚡ Quickstart

Ready to spin up your private tunnel? Navigate to the project directory and execute the main orchestration script:

    cd client-refactor/byovpn
    uv run main.py

**What happens next?** The script will automatically:
1. Generate fresh local and remote WireGuard keypairs.
2. Provision the cloud infrastructure and necessary security groups.
3. Inject a user-data script to install and securely persist WireGuard on the server.
4. Output a ready-to-use client configuration file right on your local machine. 

## 🚧 Beta Notice & Roadmap

**Status: Beta**

Currently, BYOVPN provisions infrastructure primarily on AWS EC2. While this is fantastic for on-demand, bursty usage, AWS data egress costs can add up if you are pushing heavy, continuous bandwidth through the tunnel. 

**What's Next:**
* **VPS Provider Support:** We are actively working on adding backend support for traditional, cost-effective VPS providers (like DigitalOcean, Hetzner, or Linode) to tap into flat-rate, high-bandwidth data pools suited for heavy, 24/7 VPN usage!
* **Multi-Peer Support:** Expanding our templating system to manage multiple simultaneous clients with ease.
