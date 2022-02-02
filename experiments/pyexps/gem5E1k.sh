#! /bin/bash

REPO_DIR="/OS/endhost-networking/work/sim/hejing/simbricks"
GEM5_EXE="$REPO_DIR/sims/external/gem5/build/X86/gem5.opt"
SW_EXE="$REPO_DIR/sims/net/switch/net_switch"

OUT_DIR_SER="$REPO_DIR/experiments/out/gem5Nic/3/gem5-out.server.0"
OUT_DIR_CL="$REPO_DIR/experiments/out/gem5Nic/3/gem5-out.client.0"
OUT_DIR_BASE="$REPO_DIR/experiments/out/gem5Nic/3"

CKP_DIR_SER="$REPO_DIR/experiments/out/gem5Nic/0/gem5-cp.server.0"
CKP_DIR_CL="$REPO_DIR/experiments/out/gem5Nic/0/gem5-cp.client.0"

GEM5_CONFIG="$REPO_DIR/sims/external/gem5/configs/simbricks/simbricks.py"
X86_ARGS=" --caches --l2cache --l3cache --l1d_size=32kB --l1i_size=32kB --l2_size=2MB --l3_size=32MB --l1d_assoc=8 --l1i_assoc=8 --l2_assoc=4 --l3_assoc=16 --cacheline_size=64 --cpu-clock=3GHz --sys-clock=1GHz --cpu-type=TimingSimpleCPU --mem-size=8192MB --num-cpus=1 --ddio-enabled --ddio-way-part=8 --mem-type=DDR4_2400_16x4"

KERNEL_DIR="$REPO_DIR/images/vmlinux"
IMAGE="$REPO_DIR/images/output-base/base.raw"
CFG_SER="$REPO_DIR/experiments/out/gem5Nic/0/cfg.server.0.tar"
CFG_CL="$REPO_DIR/experiments/out/gem5Nic/0/cfg.client.0.tar"

SIMBRICKS_PARAM="--simbricks-eth-lat=500 --simbricks-sync-int=500 --simbricks-poll-int=500 --simbricks-sync --simbricks-etherlink"

ETH_SER="$REPO_DIR/experiments/out/gem5Nic/0/dev.eth.server.0."
SHM_SER="$REPO_DIR/experiments/out/gem5Nic/0/dev.shm.server.0."

ETH_CL="$REPO_DIR/experiments/out/gem5Nic/0/dev.eth.clinet.0."
SHM_CL="$REPO_DIR/experiments/out/gem5Nic/0/dev.shm.client.0."

DEBUG_FLAGS="Ethernet,DMA,PciDevice,EthernetIntr"

ALL_PIDS=""
WAIT_PIDS=""

run_gem5()
{
    echo "start server"
    $GEM5_EXE --outdir=$OUT_DIR_SER \
                --debug-flags=$DEBUG_FLAGS \
                --debug-start=1276516223792 \
                $GEM5_CONFIG \
                $X86_ARGS \
                --checkpoint-dir=$CKP_DIR_SER \
                --kernel=$KERNEL_DIR \
                --disk-image=$IMAGE \
                --disk-image=$CFG_SER \
                --simbricks-eth=$ETH_SER \
                --simbricks-shm=$SHM_SER \
                $SIMBRICKS_PARAM > $OUT_DIR_SER/log.ser &

    pid=$!
    ALL_PIDS="$ALL_PIDS $pid"

    echo "start client"
    $GEM5_EXE --outdir=$OUT_DIR_CL \
                --debug-flags=$DEBUG_FLAGS \
                --debug-start=1276516223792 \
                $GEM5_CONFIG \
                $X86_ARGS \
                --checkpoint-dir=$CKP_DIR_CL \
                --kernel=$KERNEL_DIR \
                --disk-image=$IMAGE \
                --disk-image=$CFG_CL \
                --simbricks-eth=$ETH_CL \
                --simbricks-shm=$SHM_CL \
                $SIMBRICKS_PARAM > $OUT_DIR_CL/log.ser &

    child_pid=$!
    ALL_PIDS="$ALL_PIDS $child_pid"
    

}

run_switch(){

    echo "Starting switch"

    $SW_EXE -m 0 -S 500 -E 500 -s $ETH_SER -s $ETH_CL > $OUT_DIR_BASE/log.switch &
    
    pid=$!
    ALL_PIDS="$ALL_PIDS $pid"
}

cleanup() {
    echo "Cleaning up"

    for p in $ALL_PIDS ; do
        kill -KILL $p &>/dev/null
    done
    date >>$OUT_DIR_BASE/run.out
}

sighandler(){
    echo "caught Interrup, aborting..."
    cleanup
    date
    exit 1
}

trap "sighandler" SIGINT

mkdir -p $OUT_DIR_SER
mkdir -p $OUT_DIR_CL
rm  $OUT_DIR_BASE/*shm* $OUT_DIR_BASE/*eth*
rm $OUT_DIR_BASE/run.out
echo "start time" >> $OUT_DIR_BASE/run.out
date >> $OUT_DIR_BASE/run.out
run_gem5
sleep 8
run_switch
wait $child_pid

cleanup
