import figure_generation as fig_gen
import grinchfunks as gfunk


output_prefix = config["output_prefix"]
config["lineages_of_interest"] = ["B.1.1.7","B.1.351","P.1"]

rule render_report:
    input:
        metadata = config["metadata"]
    output:
        report_b117 = os.path.join(config["outdir"],"report", f"{output_prefix}_B.1.1.7.md"),
        report_b1351 = os.path.join(config["outdir"],"report", f"{output_prefix}_B.1.351.md"),
        report_p1 = os.path.join(config["outdir"],"report", f"{output_prefix}_P.1.md"),
        data = os.path.join(config["outdir"],"report","grinch_data.json")
    run:
        fig_gen.plot_figures(config["world_map_file"], config["figdir"], input.metadata, config["continent_file"], config["lineages_of_interest"],config["flight_data_b117"],config["flight_data_b1351"],config["flight_data_p1"],config["import_report_b117"],config["import_report_b1351"],config["import_report_p1"])

        shell(
        """
        data_for_website.py \
        --metadata {input.metadata:q} \
        --outdir {config[outdir]:q} \
        --lineage-info {config[lineage_info]:q} \
        --time {config[timestamp]:q} \
        --data {output.data:q} \
        --import-report-b117 {config[import_report_b117]:q} \
        --import-report-b1351 {config[import_report_b1351]:q} \
        --import-report-p1 {config[import_report_p1]:q} \
        --raw-data-b117 {config[outdir]}/figures/B.1.1.7_raw_data.csv \
        --raw-data-b1351 {config[outdir]}/figures/B.1.351_raw_data.csv \
        --raw-data-p1 {config[outdir]}/figures/P.1_raw_data.csv
        """)
        print(gfunk.green("Grinch report written to:") + f"{output.report_b117}, {output.report_b1351} and {output.report_p1}")
        