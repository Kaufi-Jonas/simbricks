#!/bin/bash
set -eux

# build tvm
mkdir -p /root
git clone --depth 1 --recursive --branch ma https://github.com/jonas-kaufmann/tvm-simbricks.git /root/tvm
cd /root/tvm
cp 3rdparty/vta-hw/config/simbricks_pci_sample.json 3rdparty/vta-hw/config/vta_config.json
mkdir build
cp cmake/config.cmake build
cd build
echo "set(USE_LLVM OFF)" >> config.cmake
echo "set(SUMMARIZE ON)" >> config.cmake
export CXXFLAGS="-D SIM_CTRL=1"
cmake ..
make -j`nproc` runtime vta

# add pre-tuned autotvm configurations
mkdir -p /root/.tvm
cd /root/.tvm
git clone --depth 1 https://github.com/tlc-pack/tophub.git tophub

export MXNET_HOME=/root/mxnet
mkdir -p $MXNET_HOME
cd $MXNET_HOME
wget https://github.com/uwsampl/web-data/raw/main/vta/models/synset.txt
