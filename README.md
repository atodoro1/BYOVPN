# 🚀 BYOVPN (Bring Your Own VPN)

Let's be honest: paying for a commercial VPN doesn't eliminate the man-in-the-middle, it just shifts your threat model from your ISP to a third-party company. You're still forced to trust someone else's server. 

BYOVPN is built around a simple idea: you should actually own your VPN. 

It automates the deployment of an ephemeral WireGuard tunnel on your own cloud infrastructure. By doing this, you hold the encryption keys, you manage the server, and you control exactly how your data is routed.

## 🗺️ Future Plans
Right now, BYOVPN provisions infrastructure on AWS EC2. While AWS is reliable, it isn't an anonymous provider. 

Moving forward, the roadmap includes:
* **Logless VPS Support:** Adding backend support for privacy-respecting VPS providers that explicitly do not keep logs, giving you a truly private foundation.
* **Multi-Peer Support:** Expanding the config generation to easily handle multiple simultaneous WireGuard clients.

## 🛠️ Prerequisites
* [`uv`](https://github.com/astral-sh/uv) installed
* [Pulumi CLI](https://www.pulumi.com/docs/install/) installed and authenticated
* Cloud credentials configured locally (e.g., `aws configure`)
* WireGuard tools (`wg`) installed locally

## ⚡ Usage

Spin up your private tunnel and generate a local client config:

```bash
cd src
uv run main.py --provider aws
```

## 💥 Teardown

Because BYOVPN is ephemeral, you can destroy the infrastructure completely the second you are done using it:

```bash
uv run main.py --provider aws --destroy
```
