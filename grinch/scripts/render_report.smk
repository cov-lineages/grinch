import figure_generation as fig_gen
import grinchfunks as gfunk


output_prefix = config["output_prefix"]

rule render_report:
    input:
        metadata = config["metadata"]
    output:
        data = os.path.join(config["outdir"],"report","grinch_data.json")
    run:
        fig_gen.plot_figures(config["world_map_file"], config["figdir"], input.metadata, config["continent_file"], config["flight_data_path"])

        shell(
        """
        data_for_website.py \
        --metadata {input.metadata:q} \
        --outdir {config[outdir]:q} \
        --variants-info {config[variants_csv]:q} \
        --data {output.data:q} 
        """)
        print(gfunk.green("Grinch reports written to:"), config["outdir"])