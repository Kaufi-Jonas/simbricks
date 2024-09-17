"""This script shows the inference result of
vta/tutorials/frontend/deploy_detection.py."""

import sys
import json
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: classify_simple.py experiment_output.json...")
        sys.exit(1)

    print ("device\tcores\tVTA config\tVTA clock\tdevice request\tmodel load\tinference\tend to end")

    for i in range(1, len(sys.argv)):
        with open(sys.argv[i], mode="r", encoding="utf-8") as file:
            exp_out = json.load(file)
        stdout = exp_out["sims"]["host."]["stdout"]
        line: str
        req_dur = 0
        load_model_dur = 0
        inf_dur = 0
        e2e_dur = 0
        for line in stdout:
            if line.startswith("<board.serconsole.con>Rep 0: Requesting remote device"):
                req_dur = int(line.split(" ")[5]) / 10**6
            if line.startswith("<board.serconsole.con>Rep 0: Sending and loading model"):
                load_model_dur = int(line.split(" ")[6]) / 10**6
            if line.startswith("<board.serconsole.con>Rep 0: Pure inference duration"):
                inf_dur = int(line.split(" ")[5]) / 10**6
            if line.startswith("<board.serconsole.con>Rep 0: End-to-end latency:"):
                e2e_dur = int(line.split(" ")[4]) / 10**6

        name_split = os.path.basename(sys.argv[i]).split("-")
        device = name_split[2]
        cores = name_split[4]
        vta_freq = name_split[5]
        vta_conf = name_split[6]

        print(f"{device}\t{cores}\t{vta_conf}\t\t{vta_freq}\t\t{req_dur:.2f}\t\t{load_model_dur:.2f}\t\t{inf_dur:.2f}\t\t{e2e_dur:.2f}")

if __name__ == "__main__":
    main()
