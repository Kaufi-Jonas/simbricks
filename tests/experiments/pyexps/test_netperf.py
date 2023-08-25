import math
import os

from results.utils import netperf

REL_DIFF = 0.05


def exp_out_filename(exp_name: str) -> str:
    exp_out = os.path.abspath(f'experiments/out/{exp_name}-1.json')
    assert os.path.exists(exp_out), \
        f'Output JSON file for experiment {exp_name} doesn\'t exist.'

    size_bytes = os.stat(exp_out).st_size
    assert size_bytes <= 100 * 10**3, \
        f'Output JSON file for experiment {exp_name} shouldn\'t be larger ' \
        'than 100 kB.'

    return exp_out


# HostSim ⨯ NICSim Tests
# ======================

# Qemu with icount / timing
# -------------------------


def test_netperf_qt_i40e_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-i40e-wire')
    )

    assert math.isclose(measured['throughput'], 546.24, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20097.33, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20991, rel_tol=REL_DIFF)


def test_netperf_qt_e1000_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-e1000-wire')
    )

    assert math.isclose(measured['throughput'], 1163.13, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20102.71, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20991, rel_tol=REL_DIFF)


def test_netperf_qt_cd_bm_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-cd_bm-wire')
    )

    assert math.isclose(measured['throughput'], 607.48, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20108.20, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20991, rel_tol=REL_DIFF)


def test_netperf_qt_cd_verilator_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-cd_verilator-wire')
    )

    assert math.isclose(measured['throughput'], 613.77, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20111.85, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20991, rel_tol=REL_DIFF)


# gem5 with timing
# ----------------


def test_netperf_gem5_i40e_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-gem5-i40e-wire')
    )

    assert math.isclose(measured['throughput'], 745.34, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20138.06, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20866, rel_tol=REL_DIFF)


def test_netperf_gem5_e1000_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-gem5-e1000-wire')
    )

    assert math.isclose(measured['throughput'], 1121.76, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20154.20, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20894, rel_tol=REL_DIFF)


def test_netperf_gem5_cd_bm_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-gem5-cd_bm-wire')
    )

    assert math.isclose(measured['throughput'], 602.19, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20138.06, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20866, rel_tol=REL_DIFF)


def test_netperf_gem5_cd_verilator_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-gem5-cd_verilator-wire')
    )

    assert math.isclose(measured['throughput'], 626.82, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20142.10, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20875, rel_tol=REL_DIFF)


# Qemu with KVM acceleration
# --------------------------


def test_netperf_qemu_i40e_wire():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qemu-i40e-wire')
    )

    assert measured['throughput'] > 0
    assert measured['latenyMean'] > 0
    assert measured['latenyTail'] > 0


# NetSim Tests
# ============


def test_netperf_qt_i40e_switch():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-i40e-switch')
    )

    assert math.isclose(measured['throughput'], 525.29, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 20097.01, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 20991, rel_tol=REL_DIFF)


def test_netperf_qt_i40e_ns3_bridge():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-i40e-ns3_bridge')
    )

    assert math.isclose(measured['throughput'], 1029.70, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 10037.40, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 10991, rel_tol=REL_DIFF)


def test_netperf_qt_i40e_ns3_dumbell():
    measured = netperf.parse_netperf_run(
        exp_out_filename('netperf-qt-i40e-ns3_dumbell')
    )

    assert math.isclose(measured['throughput'], 9.63, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyMean'], 10037.69, rel_tol=REL_DIFF)
    assert math.isclose(measured['latenyTail'], 10991, rel_tol=REL_DIFF)
