import math

import simbricks.orchestration.experiments as exp
import simbricks.orchestration.simulators as sim
import simbricks.orchestration.nodeconfig as node
import itertools
import os

experiments = []

# Experiment parameters
host_variants = ["qk", "qt", "gt", "gk", "ga", "simics"]
rtl_variants = ["verilator", "gate", "rtl"]
inference_device_opts = [
    node.TvmDeviceType.VTA,
    node.TvmDeviceType.CPU,
    node.TvmDeviceType.CPU_ARM64,
]
vta_clk_freq_opts = [100, 167]
vta_batch_opts = [1]
vta_block_opts = [16]
model_name_opts = [
    "resnet18_v1",
    "resnet34_v1",
    "resnet50_v1",
]
core_opts = [1, 4]
log_opts = ["l", "nl"]


class TvmClassifyLocal(node.AppConfig):
    """Runs inference for detection model locally, either on VTA or the CPU."""

    def __init__(self):
        super().__init__()
        self.pci_vta_id = 0
        self.target_device = node.TvmDeviceType.VTA
        self.target_host = node.TvmDeviceType.CPU
        self.repetitions = 1
        self.batch_size = 1
        self.vta_batch = 1
        self.vta_block = 16
        self.model_name = "resnet18_v1"
        self.debug = True
        self.env_simulator = None

    def config_files(self):
        # mount TVM inference script in simulated server under /tmp/guest
        files = {
            "deploy_classification-infer.py": open(
                "/home/jonask/Repos/tvm-simbricks/vta/tutorials/frontend/deploy_classification-infer.py",
                "rb",
            ),
            "cat.jpg": open("/home/jonask/Downloads/cat.jpg", "rb"),
        }
        for library in os.listdir(self.mxnet_dir):
            if not library.endswith(".so"):
                continue
            files[library] = open(f"{self.mxnet_dir}/{library}", "rb")
        files["cma_malloc.ko"] = open(
            "/home/jonask/Repos/tvm-simbricks/3rdparty/cma_malloc/module/cma_malloc.ko",
            "rb",
        )
        return files

    def prepare_pre_cp(self) -> list[str]:
        cmds = super().prepare_pre_cp()
        cmds.extend(
            [
                'echo \'{"TARGET" : "simbricks-pci", "HW_VER" : "0.0.2",'
                ' "LOG_INP_WIDTH" : 3, "LOG_WGT_WIDTH" : 3,'
                ' "LOG_ACC_WIDTH" : 5, "LOG_BATCH" :'
                f' {int(math.log2(self.vta_batch))}, "LOG_BLOCK" :'
                f' {int(math.log2(self.vta_block))}, "LOG_UOP_BUFF_SIZE" :'
                ' 15, "LOG_INP_BUFF_SIZE" : 15, "LOG_WGT_BUFF_SIZE" : 18,'
                ' "LOG_ACC_BUFF_SIZE" : 17 }\' >'
                " /root/tvm/3rdparty/vta-hw/config/vta_config.json"
            ]
        )
        for library in os.listdir(self.mxnet_dir):
            if not library.endswith(".so"):
                continue
            cmds.append(f"ln -sf /tmp/guest/{library} /root/mxnet/{library}")
        cmds.append("insmod /tmp/guest/cma_malloc.ko")
        return cmds

    def run_cmds(self, node):
        cmds = []
        if self.target_device.is_cpu():
            cmds.extend(
                ["python3 -m tvm.exec.rpc_server --port=9091 &", "sleep 6"]
            )
        else:
            cmds.extend(
                [
                    (
                        f"VTA_DEVICE=0000:00:{(self.pci_vta_id):02x}.0"
                        " VTA_DRY_RUN_FILE=/tmp/vta_dry_run python3 -m"
                        " vta.exec.rpc_server --port=9091 &"
                    ),
                    "sleep 12",
                ]
            )
        # define commands to run on simulated server
        cmds.extend(
            [
                "export VTA_RPC_HOST=127.0.0.1",
                "export VTA_RPC_PORT=9091",
                "m5 checkpoint",
                # run warmup inference
                "touch /tmp/vta_dry_run",
                (
                    "python3 /tmp/guest/deploy_classification-infer.py"
                    " /root/mxnet"
                    f" {self.target_device.value} {self.target_host.value} {self.model_name} /tmp/guest/cat.jpg"
                    f" {self.batch_size} {self.repetitions} {int(self.debug)} 0"
                ),
                "rm /tmp/vta_dry_run",
            ]
        )
        if self.env_simulator is not None:
            cmds.append(f"export SIMULATOR={self.env_simulator}")
            # run actual inference
        cmds.extend(
            [
                (
                    "python3 /tmp/guest/deploy_classification-infer.py"
                    " /root/mxnet"
                    f" {self.target_device.value} {self.target_host.value} {self.model_name} /tmp/guest/cat.jpg"
                    f" {self.batch_size} {self.repetitions} {int(self.debug)} 0"
                ),
            ]
        )
        return cmds


class VtaNode(node.NodeConfig):

    def __init__(self) -> None:
        super().__init__()
        # Use locally built disk image
        self.disk_image = "vta"
        # Bump amount of system memory
        self.memory = 2 * 1024
        # Reserve physical range of memory for the VTA user-space driver
        self.kcmd_append = "cma=512M@0G-4G"

    def prepare_pre_cp(self):
        # Define commands to run before application to configure the server
        cmds = super().prepare_pre_cp()
        cmds.extend(
            [
                "mount -t proc proc /proc",
                "mount -t sysfs sysfs /sys",
                # Make TVM's Python framework available
                "export PYTHONPATH=/root/tvm/python:${PYTHONPATH}",
                "export PYTHONPATH=/root/tvm/vta/python:${PYTHONPATH}",
                "export MXNET_HOME=/root/mxnet",
                # Set up loopback interface so the TVM inference script can
                # connect to the RPC server
                "ip link set lo up",
                "ip addr add 127.0.0.1/8 dev lo",
                # Make VTA device available for control from user-space via
                # VFIO
                (
                    "echo 1"
                    " >/sys/module/vfio/parameters/enable_unsafe_noiommu_mode"
                ),
                'echo "dead beef" >/sys/bus/pci/drivers/vfio-pci/new_id',
            ]
        )
        return cmds


# Build experiment for all combinations of parameters
for (
    host_var,
    inference_device,
    vta_clk_freq,
    vta_batch,
    vta_block,
    model_name,
    cores,
    rtl_variant,
    log_opt,
) in itertools.product(
    host_variants,
    inference_device_opts,
    vta_clk_freq_opts,
    vta_batch_opts,
    vta_block_opts,
    model_name_opts,
    core_opts,
    rtl_variants,
    log_opts,
):
    experiment = exp.Experiment(
        f"{model_name}-{inference_device.value}-{host_var}-{cores}-{vta_clk_freq}-{rtl_variant}-{log_opt}"
    )
    pci_vta_id = 2
    sync = False
    if host_var == "qk":
        HostClass = sim.QemuHost
    elif host_var == "qt":
        HostClass = sim.QemuIcountHost
        sync = True
    elif host_var == "gt":
        pci_vta_id = 0
        HostClass = sim.Gem5Host
        experiment.checkpoint = True
        sync = True
    elif host_var == "ga":
        pci_vta_id = 3

        class CustomGem5ArmHost(sim.Gem5ArmHost):

            def __init__(self, node_config: sim.NodeConfig) -> None:
                super().__init__(node_config)
                self.cpu_freq = "1200MHz"
                self.cpu_type = "hpi"
                self.variant = "fast"

        HostClass = CustomGem5ArmHost
        experiment.checkpoint = True
        sync = True
    elif host_var == "gk":
        pci_vta_id = 0
        HostClass = sim.Gem5KvmHost
        sync = False
    elif host_var == "simics":
        HostClass = sim.SimicsHost
        pci_vta_id = 0x0B

    # Instantiate server
    server_cfg = VtaNode()
    server_cfg.nockp = True
    server_cfg.cores = cores
    if host_var == "simics":
        server_cfg.disk_image += "-simics"
        server_cfg.kcmd_append = ""
    server_cfg.app = TvmClassifyLocal()
    if host_var in ["gt", "gk", "ga"] and log_opt == "l":
        server_cfg.app.env_simulator = "gem5"
    server_cfg.app.target_device = inference_device
    if inference_device.is_cpu():
        server_cfg.app.target_host = inference_device
    if host_var == "ga":
        server_cfg.app.target_host = node.TvmDeviceType.CPU_ARM64
        server_cfg.disk_image = "vta"
    server_cfg.app.vta_batch = vta_batch
    server_cfg.app.vta_block = vta_block
    server_cfg.app.model_name = model_name
    server_cfg.app.pci_vta_id = pci_vta_id
    server = HostClass(server_cfg)
    # Whether to synchronize VTA and server
    server.sync = sync
    # Wait until server exits
    server.wait = True

    # Instantiate and connect VTA PCIe-based accelerator to server
    if inference_device == node.TvmDeviceType.VTA:
        if rtl_variant == "verilator":
            vta = sim.VTADev()
            vta.batch = vta_batch
            vta.block = vta_block
        elif rtl_variant == "gate":
            vta = sim.XsimDev(
                "vta_xsim",
                100,
                "/local/jkaufman/vivado_vta/vivado_vta.sim/sim_1/synth/func/xsim/vta_sim_vlog.prj",
                "vta_sim",
            )
            if log_opt == "l":
                vta.saif_sampling_period_ns = 10 * 10**6
                vta.saif_sampling_length_ns = 10 * 10**6
        elif rtl_variant == "rtl":
            vta = sim.XsimDev(
                "vta_xsim_rtl",
                100,
                "/local/jkaufman/vivado_vta/vivado_vta.sim/sim_1/behav/xsim/vta_sim_behav_vlog.prj",
                "vta_sim_behav",
            )
            vta.libs = []
            if log_opt == "l":
                vta.saif_sampling_period_ns = 10 * 10**6
                vta.saif_sampling_length_ns = 10 * 10**6
        else:
            raise NameError(f"Unknown rtl_variant {rtl_variant}")
        vta.clock_freq = vta_clk_freq

        server.add_pcidev(vta)
        if host_var == "simics":
            server.debug_messages = False
            server.start_ts = vta.start_tick = int(63 * 10**12)

    server.pci_latency = server.sync_period = vta.pci_latency = (
        vta.sync_period
    ) = 200

    # Add both simulators to experiment
    experiment.add_host(server)
    if inference_device == node.TvmDeviceType.VTA:
        experiment.add_pcidev(vta)

    experiments.append(experiment)
