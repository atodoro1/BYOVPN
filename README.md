# 🚀 BYOVPN (Bring Your Own VPN)

Choosing a commercial VPN just shifts your threat model from your ISP to a third-party company. The whole point of BYOVPN is that you own your VPN. 

By automating the deployment of an ephemeral WireGuard tunnel on your own cloud infrastructure, you hold the keys, manage the server, and choose exactly how your data is handled.

## 🚧 Status & Roadmap
* **Current:** Provisions infrastructure on AWS EC2.
* **Future:** Adding support for various privacy-respecting VPS providers that do not keep logs.

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

Destroy the infrastructure completely when you are done:

```bash
uv run main.py --provider aws --destroy
```