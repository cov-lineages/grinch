import csv
import os

list_of_stems = config["file_stems"].split(",")

rule all:
    input:
        expand(os.path.join(config["outdir"],"1","lineages.{stem}.csv"), stem=list_of_stems),
        os.path.join(config["outdir"],"2","lineage_report.csv")

rule pangolin:
    input:
        fasta = os.path.join(config["outdir"],"1", "{stem}.fasta")
    output:
        csv = os.path.join(config["outdir"],"1","lineages.{stem}.csv")
    threads:
        1
    shell:
        "pangolin {input.fasta} --outdir {config[outdir]}/1 --outfile {output.csv}"

rule gather_lineages:
    input:
        expand(os.path.join(config["outdir"],"1","lineages.{stem}.csv"), stem=list_of_stems)
    output:
        csv = os.path.join(config["outdir"],"2","lineage_report.csv")
    run:
        
        with open(output.csv,"w") as fw:
            fw.write("sequence_name,lineage,conflict,pangolin_version,pangoLEARN_version,pango_version,status,note\n")
            for i in input:
                with open(i,"r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tax = row["taxon"]
                        lineage = row["lineage"]
                        probability = row["conflict"]
                        pangolin_version = row["pangolin_version"]
                        pango_version = row["pango_version"]
                        pangoLEARN_version = row["pangoLEARN_version"]
                        status = row["status"]
                        note = row["note"]
                        fw.write(f"{tax},{lineage},{probability},{pangolin_version},{pangoLEARN_version},{pango_version},{status},{note}\n")

