#!/bin/bash
source /home/s1680070/.bashrc_conda
conda activate grinch

TODAY=$(date +%F_%H%M%S)
echo "running $TODAY report"
cd /home/shared/grinch && git pull #gets any updates to the reports in the data directory

python setup.py install

grinch -t 40 -i /home/shared/grinch/grinch/data/config.yaml --outdir "/home/shared/$TODAY" --output-prefix global_report

cd /home/shared/lineages-website && git pull

python /home/shared/grinch/grinch/scripts/update_website.py --website-dir /home/shared/lineages-website -m /home/shared/$TODAY/2/lineages.metadata.csv -n /home/shared/pangoLEARN/pangoLEARN/supporting_information/lineage_notes.txt -o /home/shared/lineages-website/_data/lineage_data.json

cp /home/shared/$TODAY/report/global_report_B.1.1.7.md /home/shared/lineages-website/global_report_B.1.1.7.md
cp /home/shared/$TODAY/report/global_report_B.1.351.md /home/shared/lineages-website/global_report_B.1.351.md
cp /home/shared/$TODAY/report/global_report_P.1.md /home/shared/lineages-website/global_report_P.1.md
cp /home/shared/$TODAY/report/grinch_data.json /home/shared/lineages-website/_data/grinch_data.json

cp /home/shared/$TODAY/figures/*.svg /home/shared/lineages-website/assets/images/

cp /home/shared/$TODAY/2/lineages.metadata.csv /home/shared/lineages-website/_data/lineages.metadata.csv

cd /home/shared/lineages-website && git pull

git add /home/shared/lineages-website/global_report_*.md
git add /home/shared/lineages-website/_data/lineages.metadata.csv
git add /home/shared/lineages-website/_data/lineage_data.json
git add /home/shared/lineages-website/_data/grinch_data.json
git add /home/shared/lineages-website/assets/images/*.svg

git commit -m "updating new variant report $TODAY"
git push

