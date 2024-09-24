import simbricks.orchestration.experiments as exp
import simbricks.orchestration.nodeconfig as node
import simbricks.orchestration.simulators as sim
import simbricks.orchestration.simulator_utils as sim_utils
import itertools

experiments = []
host_variants = ['qk', 'gt']
num_clients_opts = [1, 4, 8]
num_servers_opts = [1, 2, 4]
num_vta_per_server_opts = [1]
pci_latency_opts = [400]
net_latency_opts = [1000]

for host_var, num_clients, num_servers, num_vta_per_server, pci_latency, net_latency in itertools.product(
    host_variants, num_clients_opts, num_servers_opts, num_vta_per_server_opts, pci_latency_opts, net_latency_opts
):
    experiment = exp.Experiment(
        f'tvm_matmul_dist-{host_var}-{num_clients}-{num_servers}'
    )
    experiment.checkpoint = False

    pci_vta_id_start = 1
    sync = True
    if host_var == 'qk':
        HostClass = sim.QemuHost
        pci_vta_id_start = 3
        sync = False
    elif host_var == 'gt':
        HostClass = sim.Gem5Host

    switch = sim.SwitchNet()
    # switch.eth_latency = switch.sync_period = net_latency
    switch.name = "switch0"
    switch.sync = sync
    experiment.add_network(switch)

    tracker = sim_utils.create_basic_hosts(
        experiment,
        1,
        "tvm_tracker",
        switch,
        sim.I40eNIC,
        HostClass,
        node.i40eLinuxTvmNode,
        node.TvmTracker
    )[0]
    # tracker.node_config.cores = 2
    tracker.node_config.nockp = not experiment.checkpoint
    tracker.node_config.drivers.append('i40e')

    servers = sim_utils.create_basic_hosts(
        experiment,
        num_servers,
        "vta_server",
        switch,
        sim.I40eNIC,
        HostClass,
        node.i40eLinuxVtaNode,
        object,
        2
    )
    for server in servers:
        app = node.VtaRpcServerWTracker()
        app.tracker_host = tracker.node_config.ip
        app.pci_device_id = [
            f'0000:00:{(pci_vta_id_start + i):02d}.0'
            for i in range(num_vta_per_server)
        ]
        server.node_config.app = app
        server.node_config.nockp = not experiment.checkpoint
        # server.node_config.cores = 2
        server.node_config.drivers.append('i40e')

        for i in range(num_vta_per_server):
            vta = sim.VTADev()
            vta.name = f'vta_{i}.{server.name}'
            vta.clock_freq = 150
            vta.sync_mode = 1 if sync else 0
            vta.pci_latency = vta.sync_period = pci_latency
            server.add_pcidev(vta)
            experiment.add_pcidev(vta)

    clients = sim_utils.create_basic_hosts(
        experiment,
        num_clients,
        "tvm_client",
        switch,
        sim.I40eNIC,
        HostClass,
        node.i40eLinuxTvmNode,
        object,
        2 + num_servers
    )
    for client in clients:
        app = node.VtaMatMulWTracker()
        app.tracker_host = tracker.node_config.ip
        # client.node_config.cores = 2
        client.node_config.app = app
        client.node_config.nockp = not experiment.checkpoint
        client.node_config.drivers.append('i40e')
        client.wait = True

    for pcidev in experiment.pcidevs:
        pcidev.sync_mode = 1 if sync else 0

    experiments.append(experiment)
