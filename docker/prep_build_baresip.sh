#!/bin/bash

set -euxo pipefail

LIBRE_VERSION=3.0.0
BARESIP_VERSION=3.0.0

echo "deb-src http://ftp.de.debian.org/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list.d/sources-src.list
apt-get update

# Install build dependencies for baresip
apt-get -qq install -y \
    wget \
    build-essential \
    pkgconf \
    cmake \
    libv4l-dev

apt-get -qq build-dep -y baresip
