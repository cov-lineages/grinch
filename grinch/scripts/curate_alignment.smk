import csv
from Bio import SeqIO
import os
import collections

config["trim_start"] = 265
config["trim_end"] = 29674


rule all:
    input:
        os.path.join(config["outdir"],"alignment.filtered.fasta"),
        os.path.join(config["outdir"],"decision_tree_rules.txt"),
        os.path.join(config["outdir"],"lineage_recall_report.txt")

rule filter_alignment:
    input:
        csv = config["lineages_csv"],
        fasta = os.path.join(config["datadir"],"0","gisaid.UH.RD.aligned.fasta"),
        full_csv = os.path.join(config["datadir"],"2","lineages.metadata.csv"),
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
        

rule run_training:
    input:
        fasta = os.path.join(config["outdir"],"alignment.filtered.fasta"),
        csv = os.path.join(config["outdir"],"lineages.metadata.filtered.csv"),
        reference = config["reference"]
    output:
        headers = os.path.join(config["outdir"],"decisionTreeHeaders_v1.joblib"),
        model = os.path.join(config["outdir"],"decisionTree_v1.joblib"),
        txt = os.path.join(config["outdir"],"training_summary.txt")
    shell:
        """
        python /raid/shared/grinch/grinch/scripts/pangoLEARNDecisionTree_v1.py \
        {input.csv:q} \
        {input.fasta} \
        {input.reference:q} \
        {config[outdir]} \
        > {output.txt:q}
        """

rule get_recall:
    input:
        txt = rules.run_training.output.txt
    output:
        txt = os.path.join(config["outdir"],"lineage_recall_report.txt")
    shell:
        """
        python /raid/shared/grinch/grinch/scripts/processOutputFile.py {input.txt} > {output.txt}
        """

rule get_decisions:
    input:
        headers = os.path.join(config["outdir"],"decisionTreeHeaders_v1.joblib"),
        model = os.path.join(config["outdir"],"decisionTree_v1.joblib"),
        txt = rules.run_training.output.txt
    output:
        txt = os.path.join(config["outdir"],"decision_tree_rules.txt")
    shell:
        """
        python /raid/shared/grinch/grinch/scripts/getDecisionTreeRules.py \
        {input.model:q} {input.headers:q} {input.txt:q} \
        > {output.txt:q}
        """
