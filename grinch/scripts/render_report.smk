from grinch.utils import grinchfunks as gfunk
from grinch.figure_generation import figurefunks as fig_gen


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
        --data {output.data:q} 
        """)
