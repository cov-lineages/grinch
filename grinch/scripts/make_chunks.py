#!/usr/bin/env python3
import sys
import math
from Bio import SeqIO


fasta_in = sys.argv[1]
outdir = sys.argv[2]
pref = fasta_in.split(".")[0]
pref = pref.split("/")[-1]
pref = outdir +'/' + pref
record_counter = 0
with open(fasta_in, "r") as f:
    for record in SeqIO.parse(f, "fasta"):
        record_counter += 1

n_chunks = math.ceil(record_counter / 10000)

file_handles = [open(pref + "_" + str(i) + ".fasta", "w") for i in range(n_chunks)]

chunk_counter = 0
record_counter = 0
with open(fasta_in, "r") as f:
    for record in SeqIO.parse(f, "fasta"):
        file_handles[chunk_counter].write(">" + record.id + "\n")
        file_handles[chunk_counter].write(str(record.seq) + "\n")

        record_counter += 1
        if record_counter % 10000 == 0:
            chunk_counter += 1

for fh in file_handles:
    fh.close()
