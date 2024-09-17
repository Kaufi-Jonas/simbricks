import sys
import json
import re
import csv


def extract_durations(stdout: list[str]):
    durations = []

    sleeping_for_rgx = r"^<board.serconsole.con>Rep [0-9]+ sleeping for [0-9]+ s"
    sleeping_for_idx = []

    for idx in range(len(stdout)):
        if re.match(sleeping_for_rgx, stdout[idx]):
            sleeping_for_idx.append(idx)

    for idx in sleeping_for_idx:
        sleep_dur = int(stdout[idx].split(" ")[4])
        req_dur = int(stdout[idx + 1].split(" ")[5]) / 10**6
        load_model_dur = int(stdout[idx + 2].split(" ")[6]) / 10**6
        inf_dur = int(stdout[idx + 3].split(" ")[5]) / 10**6
        e2e_dur = int(stdout[idx + 4].split(" ")[4]) / 10**6
        durations.append([sleep_dur, req_dur, load_model_dur, inf_dur, e2e_dur])

    return durations


def main():
    if len(sys.argv) != 3:
        print("Usage: classify_dist.py experiment_output.json output.csv")
        sys.exit(1)

    with open(sys.argv[1], mode="r", encoding="utf-8") as file:
        exp_out = json.load(file)

    durations = []
    sim: str
    for sim in exp_out["sims"].keys():
        if sim.startswith("host.tvm_client."):
            durations.extend(extract_durations(exp_out["sims"][sim]["stdout"]))

    # write durations to csv
    with open(sys.argv[2], 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "sleep [s]",
            "requesting device [ms]",
            "load model [ms]",
            "inference [ms]",
            "end-to-end [ms]"
        ])
        writer.writerows(durations)


if __name__ == "__main__":
    main()
