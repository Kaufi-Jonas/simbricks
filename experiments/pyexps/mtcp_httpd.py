import modes.experiments as exp
import modes.simulators as sim
import modes.nodeconfig as node

configs = [
    (node.I40eLinuxNode, node.HTTPDLinux, node.HTTPCLinux, 'linux'),
    (node.I40eLinuxNode, node.HTTPDLinuxRPO, node.HTTPCLinux, 'linuxrpo'),
    (node.MtcpNode, node.HTTPDMtcp, node.HTTPCMtcp, 'mtcp')
    ]

server_cores = 1
client_cores = 1
num_clients = 1
connections = 1024
file_size = 64

experiments = []

for (nodec, appc, clientc, label) in configs:
    e = exp.Experiment('qemu-ib-switch-mtcp_httpd-%s' % (label))
    e.timeout = 5* 60

    net = sim.SwitchNet()
    e.add_network(net)

    servers = sim.create_basic_hosts(e, 1, 'server', net, sim.I40eNIC,
            sim.QemuHost, nodec, appc)

    clients = sim.create_basic_hosts(e, num_clients, 'client', net, sim.I40eNIC,
            sim.QemuHost, nodec, clientc, ip_start = 2)

    for h in servers:
        h.node_config.cores = server_cores
        h.node_config.app.threads = server_cores
        h.node_config.app.file_size = file_size
        h.sleep = 10

    for c in clients:
        c.node_config.cores = client_cores
        c.node_config.app.threads = client_cores
        c.node_config.app.server_ip = servers[0].node_config.ip
        c.node_config.app.max_msgs_conn = 0
        c.node_config.app.max_flows = \
            int(connections / num_clients)
    clients[-1].wait = True

    for h in servers + clients:
        h.node_config.disk_image = 'mtcp'
    experiments.append(e)
