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

import simbricks.orchestration.experiments as exp
import simbricks.orchestration.nodeconfig as node
import simbricks.orchestration.simulators as sim
from simbricks.orchestration.simulator_utils import create_basic_hosts

host_types = ['gt']
nic_types = ['ib']
net_types = ['sw']
app_types = ['sleep', 'busy']

num_cores = 1
n_client = 1

experiments = []

for host_type in host_types:
    for nic_type in nic_types:
        for net_type in net_types:
            for app_type in app_types:

                e = exp.Experiment(
                    'noTraf-' + host_type + '-' + nic_type + '-' + net_type +
                    '-' + app_type
                )

                # network
                if net_type == 'sw':
                    net = sim.SwitchNet()
                elif net_type == 'br':
                    net = sim.NS3BridgeNet()
                else:
                    raise NameError(net_type)
                e.add_network(net)

                # host
                if host_type == 'qemu':
                    HostClass = sim.QemuHost
                elif host_type == 'qt':
                    HostClass = sim.QemuICountHost
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

                # create a host
                clients = create_basic_hosts(
                    e,
                    n_client,
                    'client',
                    net,
                    NicClass,
                    HostClass,
                    NcClass,
                    node.NoTraffic,
                    ip_start=2
                )

                clients[n_client - 1].wait = True

                for c in clients:
                    c.cpu_freq = '3GHz'
                    c.node_config.cores = num_cores
                    # is busy
                    if app_type == 'sleep':
                        c.node_config.app.is_sleep = 1
                    else:
                        c.node_config.app.is_sleep = 0

                print(e.name)

                # add to experiments
                experiments.append(e)
