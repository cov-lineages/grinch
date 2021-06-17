#!/bin/bash

# may need something similar to this: source /home/s1680070/.bashrc_conda

conda activate grinch

cd ~/git/pango-designation && git pull #gets any updates to the reports in the data directory

cd ~/git/grinch && git pull #gets any updates to the reports in the data directory
pip install .

TODAY=$(date +%F)
METADATA=/localdisk/home/shared/raccoon-dog/$TODAY_gisaid/publish/gisaid/gisaid_$TODAY_all_metadata.csv

grinch -t 10 -m $METADATA --outdir "/localdisk/home/shared/raccoon-dog/$TODAY_website" --output-prefix global_report

cd ~/git/lineages-website && git pull

python ~/git/grinch/grinch/scripts/update_website.py --website-dir ~/git/lineages-website -m $METADATA -d ~/git/pango-designation/lineages.csv -n ~/git/pango-designation/lineage_notes.txt -o ~/git/lineages-website/_data/lineage_data.json -a ~/git/pango-designation/pango_designation/alias_key.json

cp /localdisk/home/shared/raccoon-dog/$TODAY_website/report/global_report_B.1.1.7.md ~/git/lineages-website/global_report_B.1.1.7.md
cp /localdisk/home/shared/raccoon-dog/$TODAY_website/report/global_report_B.1.351.md ~/git/lineages-website/global_report_B.1.351.md
cp /localdisk/home/shared/raccoon-dog/$TODAY_website/report/global_report_P.1.md ~/git/lineages-website/global_report_P.1.md
cp /localdisk/home/shared/raccoon-dog/$TODAY_website/report/grinch_data.json ~/git/lineages-website/_data/grinch_data.json

cp /localdisk/home/shared/raccoon-dog/$TODAY_website/figures/*.svg ~/git/lineages-website/assets/images/

git add ~/git/lineages-website/lineages.md
git add ~/git/lineages-website/lineages/lineages*/*.md
git add ~/git/lineages-website/global_report_*.md
git add ~/git/lineages-website/_data/lineage_data.json
git add ~/git/lineages-website/_data/grinch_data.json
git add ~/git/lineages-website/assets/images/*.svg

git commit -m "updating website $TODAY"
git push
