#!/bin/bash
eval "$(conda shell.bash hook)"
#source ~/.bashrc_conda

conda activate grinch

cd ~/git/pango-designation && git pull #gets any updates to the reports in the data directory

cd ~/git/grinch && git pull #gets any updates to the reports in the data directory
pip install .

if [ -z "$1" ]; then
  TODAY=`date +'%Y-%m-%d'`
else
  TODAY=$1
fi

echo "RUN GRINCH for date $TODAY"
METADATA=/localdisk/home/shared/raccoon-dog/"$TODAY"_gisaid/publish/gisaid/gisaid_"$TODAY"_all_metadata.csv
echo "Using metadata $METADATA"
which grinch
echo $PWD
grinch -t 10 -m $METADATA --outdir /localdisk/home/shared/raccoon-dog/"$TODAY"_website --output-prefix global_report -a report_only

echo "Update website"
cd ~/git/lineages-website && git pull

python ~/git/grinch/grinch/scripts/update_website.py --website-dir ~/git/lineages-website -m $METADATA -d ~/git/pango-designation/lineages.csv -n ~/git/pango-designation/lineage_notes.txt \
  -o ~/git/lineages-website/_data/lineage_data.json -a ~/git/pango-designation/pango_designation/alias_key.json

echo "Place output files"
cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/report/global_report_B.1.1.7.md ~/git/lineages-website/global_report_B.1.1.7.md
cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/report/global_report_B.1.351.md ~/git/lineages-website/global_report_B.1.351.md
cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/report/global_report_P.1.md ~/git/lineages-website/global_report_P.1.md
cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/report/grinch_data.json ~/git/lineages-website/_data/grinch_data.json

cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/figures/*.svg ~/git/lineages-website/assets/images/

git add ~/git/lineages-website/lineages.md
git add ~/git/lineages-website/lineages/*.md
git add ~/git/lineages-website/lineages/*/*.md
git add ~/git/lineages-website/global_report_*.md
git add ~/git/lineages-website/_data/lineage_data.json
git add ~/git/lineages-website/_data/grinch_data.json
git add ~/git/lineages-website/assets/images/*.svg
git add ~/git/lineages-website/_data/lineages.yml
git add ~/git/lineages-website/data/lineages.yml

git commit -m "updating website $TODAY"
git push

echo "Finished!"
