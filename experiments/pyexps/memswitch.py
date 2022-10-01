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

experiments = []
num_of_netmem =[1, 2, 3, 4]

class MemTest(node.AppConfig):
    def __init__(self, addr):
        self.addr = addr

    def run_cmds(self, node):
        return [
            f'busybox devmem 0x{self.addr:x} 64 0x42',
            f'busybox devmem 0x{self.addr:x} 64'
        ]

# AS_ID,VADDR_START(include),VADDR_END(not include),MEMNODE_MAC,PHYS_START
sw_mem_map = [(0, 0, 1073741824, '00:00:00:00:00:02', 0)]

for h in ['gk']:
    e = exp.Experiment('memsw-' + h)
    e.checkpoint = False

    mem = sim.MemNIC()
    mem.name = 'mem0'
    mem.addr = 0x2000000000 #0x2000000000000000
    mem.mac = '00:00:00:00:00:01'

    netmem = sim.NetMem()
    netmem.mac = '00:00:00:00:00:02'
    

    node_config = node.NodeConfig()
    node_config.nockp = True
    node_config.app = MemTest(mem.addr)

    net = sim.MemSwitchNet()
    for tp in sw_mem_map:
        net.mem_map.append(tp)

    e.add_network(net)

    if h == 'gk':
        host = sim.Gem5Host(node_config)
        host.cpu_type = 'X86KvmCPU'
        host.variant = 'opt'
    elif h == 'qk':
        host = sim.QemuHost(node_config)
    host.name = 'host.0'
    e.add_host(host)
    host.wait = True

    mem.set_network(net)
    netmem.set_network(net)
    e.add_memdev(mem)

    host.add_memdev(mem)

    experiments.append(e)