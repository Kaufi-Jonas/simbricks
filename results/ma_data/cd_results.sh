#!/bin/bash

for i in 100 200 400 800
do
    python results/classify_dist.py experiments/out/cd-resnet34_v1-vta-s-4-20-${i}-1x16-1.json cd-resnet34_v1-vta-s-4-20-${i}-1x16.csv
done