import simbricks.orchestration.experiments as exp
import simbricks.orchestration.nodeconfig as node
import simbricks.orchestration.simulators as sim
import simbricks.orchestration.simulator_utils as sim_utils
from simbricks.orchestration import e2e_topologies
import simbricks.orchestration.e2e_components as e2e
import itertools

experiments = []

start_tick = int(67 * 10**12)

link_rate = 1  # Gbps
link_latency = 5  # ms
bdp = int(link_rate * link_latency / 1000 * 10**9)  # Bandwidth-delay product
queue_size = bdp
mtu = 1500

host_variants = ["qk", "qt", "s"]
num_clients_opts = [20]
num_servers_opts = [4]
inference_device_opts = [
    node.TvmDeviceType.VTA,
    node.TvmDeviceType.CPU,
    node.TvmDeviceType.CPU_AVX512,
]
vta_clk_freq_opts = [100, 200, 400, 800]
vta_batch_opts = [1]
vta_block_opts = [16]
model_name_opts = [
    "resnet18_v1",
    "resnet34_v1",
    "resnet50_v1",
]

for (
    host_var,
    num_clients,
    num_servers,
    inference_device,
    vta_clk_freq,
    vta_batch,
    vta_block,
    model_name,
) in itertools.product(
    host_variants,
    num_clients_opts,
    num_servers_opts,
    inference_device_opts,
    vta_clk_freq_opts,
    vta_batch_opts,
    vta_block_opts,
    model_name_opts,
):
    experiment = exp.Experiment(
        f"cd-{model_name}-{inference_device.value}-{host_var}-{num_servers}-{num_clients}-{vta_clk_freq}-{vta_batch}x{vta_block}"
    )
    pci_vta_id_start = 1
    sync = False
    if host_var == "qk":
        HostClass = sim.QemuHost
        pci_vta_id_start = 3
    elif host_var == "qt":
        HostClass = sim.QemuIcountHost
        pci_vta_id_start = 3
        sync = True
    elif host_var == "gem5":
        HostClass = sim.Gem5Host
        sync = True
    elif host_var == "s":
        HostClass = sim.SimicsHost
        pci_vta_id_start = 0x0c
        sync = True

    # instantiate network
    net = sim.NS3E2ENet()
    topology = e2e_topologies.E2EDumbbellTopology()
    topology.data_rate = f"{link_rate}Gbps"
    topology.delay = f"{link_latency}ms"
    topology.queue_size = f"{queue_size}B"
    topology.mtu = mtu
    net.add_component(topology)
    experiment.add_network(net)

    # instantiate load balancer
    tracker = sim_utils.create_basic_hosts(
        experiment,
        1,
        "tvm_tracker",
        net,
        sim.E1000NIC,
        HostClass,
        node.E1000LinuxTvmNode,
        node.TvmTracker,
    )[0]
    tracker_net = e2e.E2ESimbricksHost(tracker.full_name())
    tracker_net.eth_latency = "1us"
    tracker_net.sync = (
        e2e.SimbricksSyncMode.SYNC_REQUIRED
        if sync
        else e2e.SimbricksSyncMode.SYNC_DISABLED
    )
    tracker_net.simbricks_component = tracker.nics[0]
    topology.add_right_component(tracker_net)

    # instantiate & configure inference servers
    servers = sim_utils.create_basic_hosts(
        experiment,
        num_servers,
        "vta_server",
        net,
        sim.E1000NIC,
        HostClass,
        node.E1000LinuxVtaNode,
        object,
        2,
    )
    for i in range(len(servers)):
        app = node.VtaRpcServerWTracker()
        app.tracker_host = tracker.node_config.ip
        app.pci_device_id = f"0000:00:{(pci_vta_id_start):02x}.0"
        servers[i].node_config.app = app

        vta = sim.VTADev()
        vta.name = f"vta{i}"
        vta.clock_freq = vta_clk_freq
        vta.batch = vta_batch
        vta.block = vta_block
        if host_var == "s":
            vta.start_tick = start_tick
        servers[i].add_pcidev(vta)
        experiment.add_pcidev(vta)

        server_net = e2e.E2ESimbricksHost(servers[i].full_name())
        server_net.eth_latency = "1us"
        server_net.sync = (
            e2e.SimbricksSyncMode.SYNC_REQUIRED
            if sync
            else e2e.SimbricksSyncMode.SYNC_DISABLED
        )
        server_net.simbricks_component = servers[i].nics[0]
        topology.add_right_component(server_net)

    # instantiate & configure clients using inference service
    clients = sim_utils.create_basic_hosts(
        experiment,
        num_clients,
        "tvm_client",
        net,
        sim.E1000NIC,
        HostClass,
        node.E1000LinuxTvmClassifyNode,
        object,
        2 + num_servers,
    )
    seed = 0
    for client in clients:
        app = node.TvmClassifyWTracker()
        app.model_name = model_name
        app.repetitions = 3
        app.batch_size = 4
        app.vta_batch = vta_batch
        app.vta_block = vta_block
        app.tracker_host = tracker.node_config.ip
        app.device = inference_device
        app.seed = seed
        seed = seed + 1
        client.node_config.app = app
        client.wait = True

        client_net = e2e.E2ESimbricksHost(client.full_name())
        client_net.eth_latency = "1us"
        client_net.sync = (
            e2e.SimbricksSyncMode.SYNC_REQUIRED
            if sync
            else e2e.SimbricksSyncMode.SYNC_DISABLED
        )
        client_net.simbricks_component = client.nics[0]
        topology.add_left_component(client_net)

    # either globally synchronize
    for dev in experiment.pcidevs:
        dev.sync_mode = 1 if sync else 0
    for host in experiment.hosts:
        host.node_config.nockp = not experiment.checkpoint

    if host_var == "s":
        for host_sim in itertools.chain(servers, clients, [tracker]):
                host_sim.start_ts = start_tick
                host_sim.node_config.disk_image = "vta_classification-simics"
                host_sim.node_config.kcmd_append = ""
                host_sim.nics[0].start_tick = start_tick

    net.init_network()
    experiments.append(experiment)
