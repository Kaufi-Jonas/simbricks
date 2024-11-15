#!/bin/bash
set -eux

# build tvm
mkdir -p /root
git clone --depth 1 --recursive --branch ma https://github.com/jonas-kaufmann/tvm-simbricks.git /root/tvm
cd /root/tvm
mkdir build
cp cmake/config.cmake build
cd build
echo "set(USE_LLVM OFF)" >> config.cmake
CMAKE_BUILD_TYPE=RelWithDebInfo cmake ..
make -j`nproc` runtime vta

# add pre-tuned autotvm configurations
mkdir -p /root/.tvm
cd /root/.tvm
git clone --depth 1 https://github.com/tlc-pack/tophub.git tophub

export MXNET_HOME=/root/mxnet
mkdir -p $MXNET_HOME
cd $MXNET_HOME
wget https://github.com/uwsampl/web-data/raw/main/vta/models/synset.txt
