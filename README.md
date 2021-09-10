# grinch

global report investigating novel coronavirus haplotypes

## Description

grinch is an analysis pipeline that populates the cov-lineages.org website. Until recently all data processing for the website was performed by the grinch pipeline. 

We now use the metadata output of https://github.com/COG-UK/datapipe and generate the aggregate macrodata, maps and figures using grinch with the option `-a report-only`. The output json files of grinch are hosted at https://github.com/cov-lineages/lineages-website/tree/master/\_data. 

This pipeline gets run daily on our local server (which we've also called grinch 🤷‍♀️), purchased thanks to [Fast Grants](https://fastgrants.org/).

## Usage

```
usage: grinch -i <config.yaml> [options]

optional arguments:
  -h, --help            show this help message and exit

input output options:
  -a ANALYSIS, --analysis ANALYSIS
                        Analysis entry point: `full` or `report_only`.
                        Default: `full`
  -i CONFIG, --config CONFIG
                        Input config file
  -j JSON, --json JSON  GISAID JSON data
  -m METADATA, --metadata METADATA
                        Input metadata for use with analysis option
  --outdir OUTDIR       Output directory. Default: current working directory
  -o OUTPUT_PREFIX, --output-prefix OUTPUT_PREFIX
                        Output prefix. Default: grinch
  --filename FILENAME   File to access.
  --url URL             URL to access.
  --username USERNAME   Username for access.
  --password PASSWORD   Password for access.

misc options:
  --tempdir TEMPDIR     Specify where you want the temporary stuff to go
                        Default: $TMPDIR
  --no-temp             Output all intermediate files
  --verbose             Print lots of stuff to screen
  --no-force            Dont force run rules
  -t THREADS, --threads THREADS
                        Number of threads
  -v, --version         show program's version number and exit
```

## General usage
We do not expect most users to run grinch themselves, particularly now as the bulk download from GISAID is pretty large. We have provided the aggregate data for both the grinch reports and lineage pages at https://github.com/cov-lineages/lineages-website and they can be seen at https://cov-lineages.org/global_report.html.

## How to deploy a local version of the grinch pipeline
- Clone this repository
- Create the conda environment from the environment.yml file with `conda env create -f environment.yml`
- `pip install .` to install grinch

## Report-only version
grinch now has a report only version of the pipeline that is the current version run to populate the cov-lineages.org/global-report.html pages. This can be run from a metadata file with sequence_name, lineage, country and sample_date fields; circumventing the need for GISAID access.
```
grinch -t 10 -a report_only -m input_metadata.csv --outdir /your/output/directory --output-prefix global_report 
```
An appropriate metadata file can be generated using a pipeline similar to https://github.com/COG-UK/datapipe

## Full grinch processing pipeline
Run grinch by supplying a custom config.yaml file of the format:
```
username: 
filename: 
url: 
password: 
world_map_file: "grinch/data/world_map.json"
flight_data_path: "grinch/data/flights"
continent_file: "grinch/data/continent_mapping.csv"
import_report_path: "grinch/data/imports"
variants_csv: "repositories/constellations/data/mutations.csv"
metadata: "lineages-website/_data/lineages.metadata.csv"
output_prefix: "global_report"
outdir: "."
command: ""
figdir: "./figures"
snps: "B.1.351=aa:E:P71L;aa:N:T205I;aa:orf1a:K1655N;aa:S:D80A;aa:S:D215G;aa:S:K417N;aa:S:A701V;aa:S:N501Y;aa:S:E484K,B.1.1.7=aa:orf1ab:T1001I;aa:orf1ab:A1708D;aa:orf1ab:I2230T;del:11288:9;del:21765:6;del:21991:3;aa:S:N501Y;aa:S:A570D;aa:S:P681H;aa:S:T716I;aa:S:S982A;aa:S:D1118H;aa:Orf8:Q27*;aa:Orf8:R52I;aa:Orf8:Y73C;aa:N:D3L;aa:N:S235F,P.1=aa:orf1ab:S1188L;aa:orf1ab:K1795Q;del:11288:9;aa:S:L18F;aa:S:T20N;aa:S:P26S;aa:S:D138Y;aa:S:R190S;aa:S:K417T;aa:S:E484K;aa:S:N501Y;aa:S:H655Y;aa:S:T1027I;aa:orf3a:G174C;aa:orf8:E92K;aa:N:P80R"
lineage_info: "grinch/data/lineage_info.json"
```
Where the username is your GISAID access username, the filename is the json file you wish to download, the url is the source of the data and the password is your access password. Note, you must have GISAID priviliges to bulk download. 

