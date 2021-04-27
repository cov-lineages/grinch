#!/bin/bash
source /home/s1680070/.bashrc_conda
conda activate grinch

TODAY=$(date +%F)
OUTDIR=data_release_$TODAY

mkdir /raid/shared/pangolearn_training/$OUTDIR

echo "training $TODAY data release"

LATEST_DATA=$(ls -td /raid/shared/2021* | head -n 1)

cd /raid/shared/pango-designation && git pull #gets any updates to the reports in the data directory
PANGO_V=$(git describe --tags --abbrev=0)

cd /raid/shared/pangolearn_training && git pull #gets any updates to the reports in the data directory

snakemake --snakefile /raid/shared/grinch/grinch/scripts/curate_alignment.smk --configfile config.yaml --cores 1 --config outdir=$OUTDIR datadir=$LATEST_DATA pangolearn_version=$TODAY pango_version=$PANGO_V

cp /raid/shared/pangolearn_training/$OUTDIR/pangolearn.init.py /raid/shared/pangoLEARN/pangoLEARN/__init__.py
cp /raid/shared/pangolearn_training/$OUTDIR/decision* /raid/shared/pangoLEARN/pangoLEARN/data/
cp /raid/shared/pangolearn_training/$OUTDIR/metadata.downsample.csv /raid/shared/pangoLEARN/pangoLEARN/data/lineages.downsample.csv
cp /raid/shared/pangolearn_training/$OUTDIR/lineages.metadata.csv /raid/shared/pango-designation/lineages.metadata.csv
cp /raid/shared/pangolearn_training/$OUTDIR/lineages.metadata.csv /raid/shared/pangoLEARN/pangoLEARN/data/lineages.metadata.csv

git add /raid/shared/pangoLEARN/pangoLEARN/__init__.py
git add /raid/shared/pangoLEARN/pangoLEARN/data/decision*
git add /raid/shared/pangoLEARN/pangoLEARN/data/lineages*


