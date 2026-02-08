# Configuring the Server and Clients

## 0. Install dependencies
```bash
$ apt install -y wireguard wireguard-tools iptables openresolv
```


## 1. Enable IPv4 forwarding on the server
```bash
# Server
sysctl -w net.ipv4.ip_forward=1
sysctl net.ipv4.ip_forward  # verify
```


## 2. Generate keys for the server
```bash
# Server
$ wg genkey | tee server-privatekey | wg pubkey > server-publickey
```


## 3. Generate keys for the client
```bash
# Client
$ wg genkey | tee client-privatekey | wg pubkey > client-publickey
```


## 4. Configure the Server
On the server, write the following config file in `/etc/wireguard`.
- Replace `$SERVER_PRIV` with the server privatekey generated in step 1.
- Replace `$CLIENT_PUB` with the client publickey generated in step 2.
- Replace `$IFACE` with the network interface you plan to use for egress.

Ensure field `Address` does not collide with your LAN IP. The port default is
`33333`, but can be changed.

```
# Filename: wg0.conf
[Interface]
## Local Address : A private IP address for wg0 interface.
Address = 10.20.10.1/24
ListenPort = 33333

## Local server privatekey
PrivateKey = $SERVER_PRIV

## The PostUp will run when the WireGuard Server starts the virtual VPN tunnel.
## The PostDown rules run when the WireGuard Server stops the virtual VPN tunnel.
## Specify the command that allows traffic to leave the server and give the VPN 
## clients access to the Internet.
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o $IFACE -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o $IFACE -j MASQUERADE

See `wg-quick(8)`.

[Peer]
# one client which will be setup to use 10.20.10.2 IP
PublicKey = $CLIENT_PUB
AllowedIPs = 10.20.10.2/32
```


## 5. Configure the Client
On the client, write the following config file in `/etc/wireguard`.
- Replace `$CLIENT_PRIV` with the client privatekey generated in step 2.
- Replace `$SERVER_PUB` with the server publickey generated in step 1.
- Replace `$ENDPOINT` with the public server endpoint.

Note that `AllowedIPs` is set to allow all, and DNS server is set to `8.8.8.8`.
`openresolv` is required for this step.

```
# Filename: client.conf

[Interface]
## Local Address : A private IP address for wg0 interface.
Address = 10.20.10.2/24
ListenPort = 33333
DNS = 8.8.8.8

## local client privateky
PrivateKey = $CLIENT_PRIV

[Peer]
# remote server public key
PublicKey = $SERVER_PUB
Endpoint = $ENDPOINT:33333
AllowedIPs = 0.0.0.0/0
```


## 6. Start the VPN server and the client
On the server, you can bring up the wireguard tunnel either directly with `wg(8)`,
or as the managed systemd unit `wg-quick@wg*`.

```
# Systemd
$ systemctl start wg-quick@wg0

# wg (last arg can also be the config file path, e.g. "./wg0.conf")
$ wg up ./wg0.conf
```

On the client, the same applies.
```
# Systemd
$ systemctl start wg-quick@client

# wg
$ wg up ./client.conf
```


## 7. Verification
```bash
$ wg show
$ systemctl status wg-quick@wg*
```


## More Information
- `wg(8)`
- `wg-quick(8)` - includes configuration file information
- [How-to blog](https://markliversedge.blogspot.com/2023/09/wireguard-setup-for-dummies.html)
- [`resolvctl` issue](https://github.com/StreisandEffect/streisand/issues/1434#issuecomment-417792239)
