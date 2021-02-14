import pandas as pd
from Bio import SeqIO
import figure_generation as fig_gen
import grinchfunks as gfunk
import csv

output_prefix = config["output_prefix"]

rule all:
    input:
        config["outdir"] + "/2/lineages.metadata.csv",
        os.path.join(config["outdir"],"report","grinch_data.json")

rule gisaid_process_json:
    input:
        json = config["json"],
        omit = config["omitted"]
    output:
        fasta = config["outdir"] + "/0/gisaid.fasta",
        metadata = config["outdir"] + "/0/gisaid.csv"
    log:
        config["outdir"] + "/logs/0_gisaid_process_json.log"
    shell:
        """
        datafunk process_gisaid_data \
          --input-json {input.json} \
          --input-metadata False \
          --exclude-file {input.omit} \
          --output-fasta {output.fasta} \
          --output-metadata {output.metadata} \
          --exclude-undated &> {log}
        """

rule gisaid_unify_headers:
    input:
        fasta = rules.gisaid_process_json.output.fasta,
        metadata = rules.gisaid_process_json.output.metadata,
    output:
        fasta = config["outdir"] + "/0/gisaid.UH.fasta",
        metadata = config["outdir"] + "/0/gisaid.UH.csv",
    log:
        config["outdir"] + "/logs/0_gisaid_unify_headers.log"
    run:

        fasta_in = SeqIO.index(str(input.fasta), "fasta")
        df = pd.read_csv(input.metadata, sep=',')

        sequence_name = []

        with open(str(output.fasta), 'w') as fasta_out:
            for i,row in df.iterrows():
                edin_header = row["edin_header"]
                new_header = edin_header.split("|")[0]
                sequence_name.append(new_header)

                try:
                    record = fasta_in[edin_header]
                    fasta_out.write(">" + new_header + "\n")
                    fasta_out.write(str(record.seq) + "\n")
                except:
                    continue

        df['sequence_name'] = sequence_name
        df.to_csv(output.metadata, index=False, sep = ",")

rule gisaid_remove_duplicates:
    input:
        fasta = rules.gisaid_unify_headers.output.fasta,
        metadata = rules.gisaid_unify_headers.output.metadata
    output:
        fasta = config["outdir"] + "/0/gisaid.UH.RD.fasta",
        metadata = config["outdir"] + "/0/gisaid.UH.RD.csv"
    log:
        config["outdir"] + "/logs/0_gisaid_remove_duplicates.log"
    shell:
        """
        fastafunk subsample \
          --in-fasta {input.fasta} \
          --in-metadata {input.metadata} \
          --group-column sequence_name \
          --index-column sequence_name \
          --out-fasta {output.fasta} \
          --sample-size 1 \
          --out-metadata {output.metadata} \
          --select-by-min-column edin_epi_day &> {log}
        """

rule align_to_reference:
    input:
        fasta = rules.gisaid_remove_duplicates.output.fasta,
        reference = config["reference"]
    params:
        trim_start = 265,
        trim_end = 29674
    output:
        fasta = os.path.join(config["outdir"],"0","gisaid.UH.RD.aligned.fasta")
    log:
        os.path.join(config["outdir"], "logs/minimap2_sam.log")
    shell:
        """
        minimap2 -a -x asm5 -t {workflow.cores} {input.reference:q} {input.fasta:q} | \
        gofasta sam toMultiAlign \
            --reference {input.reference:q} \
            --trimstart {params.trim_start} \
            --trimend {params.trim_end} \
            --pad > {output.fasta:q}
        """

rule make_chunks:
    input:
        fasta = rules.align_to_reference.output.fasta
    output:
        txt = config["outdir"] + "/1/placeholder.txt"
    shell:
        "make_chunks.py {input.fasta} {config[outdir]}/1/ && touch {output.txt}"

rule parallel_pangolin:
    input:
        snakefile = os.path.join(workflow.current_basedir,"parallel_pangolin.smk"),
        fasta = rules.make_chunks.output.txt
    params:
        chunk_dir = os.path.join(config["outdir"], "1")
    output:
        lineages = config["outdir"] + "/2/lineage_report.csv"
    threads: workflow.cores
    run:
        file_stems = []
        for r,d,f in os.walk(params.chunk_dir):
            for fn in f:
                if fn.endswith(".fasta"):
                    stem = fn.split(".")[0]
                    file_stems.append(stem)
        file_stems = ",".join(file_stems)
        shell("snakemake --nolock --snakefile {input.snakefile:q} "
                            "--config "
                            "outdir={config[outdir]} "
                            f"file_stems={file_stems} "
                            "--cores {workflow.cores}")

rule parse_variants_input:
    input:
        config["variants_csv"]
    output:
        temp(config["outdir"] + "/2/search_variants.csv")
    run:
        def record_to_variant(record):
            if record["type"] == 'deletion':
                return "del:%s:%s" %(record["nuc_location"],record["variants"])
            elif record["type"] == 'replacement':
                return "aa:%s" %record["id"]
            return None

        variant_dict = {}
        with open(input[0], 'r') as in_handle:
            reader = csv.DictReader(in_handle)
            for r in reader:
                variant = record_to_variant(r)
                order = int(r["barcode_pos"])
                variant_dict[order] = variant

        with open(output[0], 'w') as out_handle:
            for i in range(len(variant_dict)):
                out_handle.write("%s\n" %variant_dict[i])


rule type_variants:
    input:
        fasta = rules.align_to_reference.output.fasta,
        reference = config["reference"],
        variants = rules.parse_variants_input.output
    output:
        temp(config["outdir"] + "/2/typed_variants.csv")
    log:
        config["outdir"] + "/logs/2_type_variants.log"
    shell:
        """
        type_variants.py \
            --fasta-in {input.fasta:q} \
            --variants-config {input.variants:q} \
            --reference {input.reference:q} \
            --variants-out {output:q} \
            --append-genotypes &> {log}
        """

rule generate_constellation_strings:
    input:
        variants = config["variants_csv"],
        variant_calls = rules.type_variants.output
    output:
        config["outdir"] + "/2/constellation_report.csv"
    log:
        config["outdir"] + "/logs/2_generate_constellation_strings.log"
    shell:
        """
        generate_constellation.py \
            --variant-ref {input.variants:q} \
            --variant-calls {input.variant_calls:q} \
            --out-file {output[0]:q} &> {log}
        """


rule grab_metadata:
    input:
        metadata = rules.gisaid_remove_duplicates.output.metadata,
        lineages = rules.parallel_pangolin.output.lineages,
        constellations = rules.generate_constellation_strings.output
    output:
        tmp_metadata = temp(config["outdir"] + "/2/lineages.metadata.tmp.csv"),
        metadata = config["outdir"] + "/2/lineages.metadata.csv"
    log:
        config["outdir"] + "/logs/2_grab_metadata.log"
    shell:
        """
        fastafunk add_columns \
          --in-metadata {input.lineages} \
          --in-data {input.metadata} \
          --index-column sequence_name \
          --join-on sequence_name \
          --new-columns covv_accession_id country sample_date epi_week travel_history \
          --where-column epi_week=edin_epi_week country=edin_admin_0 travel_history=edin_travel sample_date=covv_collection_date \
          --out-metadata {output.tmp_metadata} &> {log}

        fastafunk add_columns \
          --in-metadata {output.tmp_metadata} \
          --in-data {input.constellations} \
          --index-column sequence_name \
          --join-on sequence_name \
          --new-columns constellation \
          --out-metadata {output.metadata} &>> {log}
        """

rule render_report:
    input:
        metadata = rules.grab_metadata.output.metadata
    output:
        data = os.path.join(config["outdir"],"report","grinch_data.json")
    run:
        fig_gen.plot_figures(config["world_map_file"], config["figdir"], input.metadata, config["continent_file"], config["lineages_of_concern"],config["flight_data_path"])

        shell(
        """
        data_for_website.py \
        --metadata {input.metadata:q} \
        --outdir {config[outdir]:q} \
        --variants-info {config[variants_csv]:q} \
        --data {output.data:q} 
        """)
        print(gfunk.green("Grinch reports written to:"), config["outdir"])
        