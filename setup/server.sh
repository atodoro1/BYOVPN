#!/usr/bin/env bash

set -e

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi


PRIVATE_KEY="private"
PUBLIC_KEY="public"

apt update -y && apt upgrade -y
apt install wireguard -y

wg genkey > $PRIVATE_KEY
chmod 600 $PRIVATE_KEY
wg publickey < $PRIVATE_KEY > $PUBLIC_KEY

ip link add wg0 type wireguard
ip addr add 10.0.0.1/24 dev wg0

wg set wg0 private-key "./$PRIVATE_KEY"

ip link set wg0 up
