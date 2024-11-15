#!/bin/bash
set -eux

apt-get update
apt-get -y install --no-install-recommends \
    build-essential \
    git \
    python-is-python3 \
    python3 \
    python3-cloudpickle \
    python3-decorator \
    python3-dev \
    python3-numpy \
    python3-pil \
    python3-psutil \
    python3-pytest \
    python3-scipy \
    python3-setuptools \
    python3-typing-extensions \
    python3-tornado \
    libtinfo-dev \
    zlib1g-dev \
    cmake \
    libedit-dev \
    libxml2-dev
