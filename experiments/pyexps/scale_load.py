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

import simbricks.experiments as exp
import simbricks.nodeconfig as node
import simbricks.simulators as sim
from simbricks.simulator_utils import create_basic_hosts

# iperf UDP Load Scalability test
# naming convention following host-nic-net
# host: gem5-timing
# nic:  cv/cb/ib
# net:  wire/switch/dumbbell/bridge
# app: UDPs

host_types = ['gt', 'qt', 'qemu']
nic_types = ['cv', 'cb', 'ib']
net_types = ['wire', 'sw', 'br']
app = ['UDPs']

rate_types = []
rate_start = 0
rate_end = 1000
rate_step = 100
for r in range(rate_start, rate_end + 1, rate_step):
    rate = f'{r}m'
    rate_types.append(rate)

experiments = []

for rate in rate_types:
    for host_type in host_types:
        for nic_type in nic_types:
            for net_type in net_types:

                e = exp.Experiment(
                    host_type + '-' + nic_type + '-' + net_type + '-Load-' +
                    rate
                )
                # network
                if net_type == 'sw':
                    NetClass = sim.SwitchNet()
                elif net_type == 'br':
                    NetClass = sim.NS3BridgeNet()
                elif net_type == 'wire':
                    NetClass = sim.WireNet()
                else:
                    raise NameError(net_type)
                e.add_network(NetClass)

                # host
                if host_type == 'qemu':
                    HostClass = sim.QemuHost
                elif host_type == 'qt':

                    def qemu_timing(node_config: node.NodeConfig):
                        h = sim.QemuHost(node_config)
                        h.sync = True
                        return h

                    HostClass = qemu_timing
                elif host_type == 'gt':
                    HostClass = sim.Gem5Host
                    e.checkpoint = True
                else:
                    raise NameError(host_type)

                # nic
                if nic_type == 'ib':
                    NicClass = sim.I40eNIC
                    NcClass = node.I40eLinuxNode
                elif nic_type == 'cb':
                    NicClass = sim.CorundumBMNIC
                    NcClass = node.CorundumLinuxNode
                elif nic_type == 'cv':
                    NicClass = sim.CorundumVerilatorNIC
                    NcClass = node.CorundumLinuxNode
                else:
                    raise NameError(nic_type)

                # create servers and clients
                servers = create_basic_hosts(
                    e,
                    1,
                    'server',
                    NetClass,
                    NicClass,
                    HostClass,
                    NcClass,
                    node.IperfUDPServer
                )

                if rate == '0m':
                    clients = create_basic_hosts(
                        e,
                        1,
                        'client',
                        NetClass,
                        NicClass,
                        HostClass,
                        NcClass,
                        node.IperfUDPClientSleep,
                        ip_start=2
                    )
                else:
                    clients = create_basic_hosts(
                        e,
                        1,
                        'client',
                        NetClass,
                        NicClass,
                        HostClass,
                        NcClass,
                        node.IperfUDPClient,
                        ip_start=2
                    )

                clients[0].wait = True
                clients[0].node_config.app.server_ip = servers[0].node_config.ip
                clients[0].node_config.app.is_last = True
                clients[0].node_config.app.rate = rate

                print(e.name)

                # add to experiments
                experiments.append(e)