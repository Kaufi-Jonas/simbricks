import os
import sys
import re
import matplotlib.pyplot as plt


def write_tcl_script(
    tcl_path: str, xpr_path: str, saif_files: list[str], output_dir: str
) -> list[str]:
    out_files = []
    lines = ['open_run impl_1']
    for saif_file in saif_files:
        lines.append('reset_switching_activity -all')
        lines.append(f'read_saif -no_strip {saif_file}')

        out_name = os.path.basename(saif_file)
        out_name = out_name.removesuffix('.saif')
        out_path = f'{output_dir}/{out_name}.txt'
        out_files.append(out_path)
        lines.append(f'report_power -no_propagation -file {out_path}')

    lines = [f'{line}\n' for line in lines]

    with open(tcl_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

    return out_files


def modify_saif_files(top_module: str, saif_files: list[str]) -> None:
    for saif_file in saif_files:
        lines = []
        with open(saif_file, mode='r', encoding='utf-8') as file:
            for line in file.readlines():
                line = re.sub(r'jpgd_sim.*$', top_module, line)
                lines.append(line)

        with open(saif_file, mode='w', encoding='utf-8') as file:
            file.writelines(lines)


def read_power_estimates(out_files: list[str]) -> list[float]:
    print('power consumption samples hier_jpgd:')
    power_nrs = []
    for out_file in out_files:
        with open(out_file, mode='r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            if re.match(r'^\| *hier_jpgd *\|.+\|', line):
                split = line.split()
                power_consumption = float(split[3])
                power_nrs.append(power_consumption)
                print(f'{power_consumption} W')

    return power_nrs


def plot_power_estimates(power_nrs: list[float]) -> None:
    plt.plot(power_nrs)
    plt.show()


def sort_filenames(files: list[str]) -> list[str]:
    file_tuples = []
    for file in files:
        dirname = os.path.dirname(file)
        basename = os.path.basename(file)
        basename = basename.removesuffix('.saif')
        split = basename.split('-')
        basename = '-'.join(split[:-1])
        file_tuples.append((f'{dirname}/{basename}', int(split[-1])))

    file_tuples.sort()
    return [f'{name}-{index}.saif' for name, index in file_tuples]


def main():
    if len(sys.argv) < 6:
        print(
            'Usage: acdsim_jpgd.py <vivado installation directory> <vivado project .xpr> <top-level module> <output dir> <saif files ...>'
        )
        sys.exit(1)

    tcl_script = '/tmp/simbricks_results_acdsim_jpgd.tcl'
    saif_files = sys.argv[5:]
    saif_files = sort_filenames(saif_files)
    # TODO last one is currently an outlier
    saif_files = saif_files[:-1]

    out_files = write_tcl_script(
        tcl_script, sys.argv[2], saif_files, sys.argv[4]
    )
    # modify_saif_files(sys.argv[3], saif_files)

    # run vivado
    # cmds = [
    #     f'source \'{sys.argv[1]}/settings64.sh\'',
    #     f'vivado -mode batch -source \'{tcl_script}\' \'{sys.argv[2]}\''
    # ]
    # cmd = ' && '.join(cmds)
    # rc = os.system(f'bash -c "{cmd}"')

    # if rc != 0:
    #     sys.exit(1)

    power_nrs = read_power_estimates(out_files)
    plot_power_estimates(power_nrs)


if __name__ == '__main__':
    main()
