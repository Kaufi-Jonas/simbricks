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

# build tvm
mkdir -p /root
git clone --depth 1 --recursive --branch ma https://github.com/jonas-kaufmann/tvm-simbricks.git /root/tvm
cd /root/tvm
cp 3rdparty/vta-hw/config/simbricks_pci_sample.json 3rdparty/vta-hw/config/vta_config.json
mkdir build
cp cmake/config.cmake build
cd build
echo "set(USE_LLVM OFF)" >> config.cmake
echo "set(BACKTRACE_ON_SEGFAULT OFF)" >> config.cmake
echo "set(SUMMARIZE ON)" >> config.cmake
cmake .. -D CMAKE_BUILD_TYPE=Debug
make VERBOSE=1 -j`nproc` runtime vta

# add pre-tuned autotvm configurations
mkdir -p /root/.tvm
cd /root/.tvm
git clone --depth 1 https://github.com/tlc-pack/tophub.git tophub

export MXNET_HOME=/root/mxnet
mkdir -p $MXNET_HOME
cd $MXNET_HOME
wget https://github.com/uwsampl/web-data/raw/main/vta/models/synset.txt
