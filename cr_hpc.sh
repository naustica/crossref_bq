#!/bin/bash
#SBATCH -p medium
#SBATCH -C scratch
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH -t 12:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nick.haupka@sub.uni-goettingen.de

module load python

python3 crossref.py

cd /scratch/users/haupka/transform && ls -1 * | xargs -P 16 gzip
