#!/bin/bash
#SBATCH -p medium
#SBATCH -C scratch
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH -t 10:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nick.haupka@sub.uni-goettingen.de

python3 start.py

