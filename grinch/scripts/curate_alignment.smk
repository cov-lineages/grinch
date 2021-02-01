import csv
from Bio import SeqIO
import os
import collections

config["trim_start"] = 265
config["trim_end"] = 29674


rule all:
    input:
        os.path.join(config["outdir"],"alignment.filtered.fasta")

rule minimap2_db_to_reference:
    input:
        fasta = config["seqs"],
        reference = config["reference"]
    output:
        sam = os.path.join(config["outdir"],"post_qc_aln.reference_mapped.sam")
    message: "Running minimap2 against the reference (early lineage A) sequence"
    log:
        os.path.join(config["outdir"],"logs","minimap2_to_reference.log")
    shell:
        """
        minimap2 -a -x asm5 {input.reference:q} {input.fasta:q} -o {output.sam:q} &> {log}
        """

rule datafunk_trim_and_pad:
    input:
        sam = rules.minimap2_db_to_reference.output.sam,
        reference = config["reference"]
    message: "Running datafunk to trim and pad against the reference"
    params:
        trim_start = config["trim_start"],
        trim_end = config["trim_end"],
        insertions = os.path.join(config["outdir"],"post_qc_query.insertions.txt")
    output:
        fasta = os.path.join(config["outdir"],"alignment.full.fasta")
    shell:
        """
        datafunk sam_2_fasta \
          -s {input.sam:q} \
          -r {input.reference:q} \
          -o {output.fasta:q} \
          -t [{params.trim_start}:{params.trim_end}] \
          --pad \
          --log-inserts 
        """

rule filter_alignment:
    input:
        csv = config["lineages_csv"],
        fasta = rules.datafunk_trim_and_pad.output.fasta,
        full_csv = config["full_csv"]
    output:
        fasta = os.path.join(config["outdir"],"alignment.filtered.fasta"),
        csv = os.path.join(config["outdir"],"lineages.metadata.filtered.csv")
    run:
        csv_len = 0
        seqs_len = 0
        lineages = {}
        with open(input.csv,"r") as f:
            for l in f:
                l = l.rstrip("\n")
                name,lineage = l.split(",")
                lineages[name]=lineage
                csv_len +=1
        with open(output.csv,"w") as fw:
            with open(input.full_csv,"r") as f:
            
                reader = csv.DictReader(f)
                header = reader.fieldnames

                writer = csv.DictWriter(fw, fieldnames=header, lineterminator="\n")
                writer.writeheader()
                for row in reader:
                    name = row["sequence_name"].replace("SouthAfrica","South_Africa")
                    if name in lineages:
                        new_row = row
                        new_row["lineage"] = lineages[name]
                        writer.writerow(new_row)
                        

        with open(output.fasta,"w") as fw:
            for record in SeqIO.parse(input.fasta, "fasta"):
                record.id = record.id.replace("SouthAfrica","South_Africa")
                if record.id in lineages:
                    fw.write(f">{record.id}\n{record.seq}\n")
                    seqs_len +=1
        
        print("Number of sequences in lineages csv", csv_len)
        print("Number of sequences found on gisaid", seqs_len)
        
