# Copyright 2021 Max Planck Institute for Software Systems, and
# National University of Singapore
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
Experiment, which simulates two hosts, one running a netperf server and the
other a client with the goal of measuring latency and throughput between them.

The goal is to compare different simulators for host, NIC, and the network in
terms of simulated network throughput and latency.
"""

import simbricks.orchestration.experiments as exp
from simbricks.orchestration import nodeconfig, simulators

host_types = ['qemu', 'qt', 'gem5', 'simics']
nic_types = ['i40e', 'e1000', 'cd_bm', 'cd_verilator']
net_types = ['wire', 'switch', 'ns3_bridge', 'ns3_dumbell']
experiments = []

# Create multiple experiments with different simulator permutations, which can
# be filtered later.
for host_t in host_types:
    for nic_t in nic_types:
        for net_t in net_types:
            e = exp.Experiment(f'netperf-{host_t}-{nic_t}-{net_t}')
            e.timeout = 2 * 60 * 60  # two hours

            # host simulator
            sync = True
            if host_t == 'qemu':
                HostClass = simulators.QemuHost
                sync = False
            elif host_t == 'qt':
                HostClass = simulators.QemuICountHost
            elif host_t == 'gem5':
                HostClass = simulators.Gem5Host
                e.checkpoint = True
            elif host_t == 'simics':
                HostClass = simulators.SimicsHost
                e.checkpoint = True
            else:
                raise NameError(f'No host simulator for key {host_t}.')

            # NIC simulator
            if nic_t == 'i40e':
                NicClass = simulators.I40eNIC
                NodeConfigClass = nodeconfig.I40eLinuxNode
            elif nic_t == 'e1000':
                NicClass = simulators.E1000NIC
                NodeConfigClass = nodeconfig.E1000LinuxNode
            elif nic_t == 'cd_bm':
                NicClass = simulators.CorundumBMNIC
                NodeConfigClass = nodeconfig.CorundumLinuxNode
            elif nic_t == 'cd_verilator':
                NicClass = simulators.CorundumVerilatorNIC
                NodeConfigClass = nodeconfig.CorundumLinuxNode
            else:
                raise NameError(f'No NIC simulator for key {nic_t}.')

            # network simulator
            if net_t == 'wire':
                net = simulators.WireNet()
            elif net_t == 'switch':
                net = simulators.SwitchNet()
            elif net_t == 'ns3_bridge':
                net = simulators.NS3BridgeNet()
            elif net_t == 'ns3_dumbell':
                net = simulators.NS3DumbbellNet()
            else:
                raise NameError(f'No net simulator for key {net_t}.')
            if sync:
                net.sync_mode = 1
            e.add_network(net)

            # set up server
            server_nic = NicClass()
            server_nic.set_network(net)
            if sync:
                server_nic.sync_mode = 1
            server_nc = NodeConfigClass()
            server_nc.ip = '10.0.0.1'
            server_nc.app = nodeconfig.NetperfServer()

            server = HostClass(server_nc)
            server.name = 'server.0'
            server.add_nic(server_nic)
            e.add_nic(server_nic)
            e.add_host(server)

            # set up client
            client_nic = NicClass()
            client_nic.set_network(net)
            if sync:
                client_nic.sync_mode = 1
            client_nc = NodeConfigClass()
            client_nc.ip = '10.0.0.2'
            client_nc.app = nodeconfig.NetperfClient()
            client_nc.app.server_ip = server_nc.ip
            client_nc.app.duration_tp = client_nc.app.duration_lat = 5

            client = HostClass(client_nc)
            client.name = 'client.0'
            client.add_nic(client_nic)
            e.add_nic(client_nic)
            e.add_host(client)

            # set more interesting Ethernet latency
            if sync:
                latency = 5 * 10**6  # 5 ms
                net.eth_latency = net.sync_period = latency
                client_nic.eth_latency = client_nic.eth_sync_period = latency
                server_nic.eth_latency = server_nic.eth_sync_period = latency

            client.wait = True
            experiments.append(e)
