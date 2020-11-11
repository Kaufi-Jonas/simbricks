#!/bin/bash

source common-functions.sh

init_out gem5-i40e-cc $1

echo "Restoring from checkpoint"

# then run with timing CPU
run_i40e_bm a
run_i40e_bm b
run_i40e_bm c
sleep 0.5
run_ns3_bridge bridge "a b c"
run_gem5 a a build/gem5-pair-i40e-server.tar TimingSimpleCPU server "-r 0 --cosim-sync --cosim-type=i40e"
run_gem5 b b build/gem5-pair-i40e-client.tar TimingSimpleCPU client "-r 0 --cosim-sync --cosim-type=i40e"
run_gem5 c c build/gem5-pair-i40e-client-2.tar TimingSimpleCPU client2 "-r 0 --cosim-sync --cosim-type=i40e"
client_pid=$!
wait $client_pid
cleanup