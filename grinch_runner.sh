#!/bin/bash
source /home/s1680070/.bashrc_conda
conda activate grinch

TODAY=$(date +%F_%H%M%S)
echo "running $TODAY report"
cd /raid/shared/pango-designation && git pull #gets any updates to the reports in the data directory

cd /raid/shared/grinch && git pull #gets any updates to the reports in the data directory

python setup.py install

grinch -t 10 -i /raid/shared/grinch/grinch/data/config.yaml --outdir "/raid/shared/$TODAY" --output-prefix global_report

cd /raid/shared/lineages-website && git pull

python /raid/shared/grinch/grinch/scripts/update_website.py --website-dir /raid/shared/lineages-website -m /raid/shared/$TODAY/2/lineages.metadata.csv -d /raid/shared/pango-designation/lineages.csv -n /raid/shared/pango-designation/lineage_notes.txt -o /raid/shared/lineages-website/_data/lineage_data.json

cp /raid/shared/$TODAY/report/global_report_B.1.1.7.md /raid/shared/lineages-website/global_report_B.1.1.7.md
cp /raid/shared/$TODAY/report/global_report_B.1.351.md /raid/shared/lineages-website/global_report_B.1.351.md
cp /raid/shared/$TODAY/report/global_report_P.1.md /raid/shared/lineages-website/global_report_P.1.md
cp /raid/shared/$TODAY/report/grinch_data.json /raid/shared/lineages-website/_data/grinch_data.json

cp /raid/shared/$TODAY/figures/*.svg /raid/shared/lineages-website/assets/images/

#cp /raid/shared/$TODAY/2/lineages.metadata.csv /home/shared/lineages-website/_data/lineages.metadata.csv
cd /raid/shared/lineages-website && git pull

git add /raid/shared/lineages-website/lineages.md
git add /raid/shared/lineages-website/lineages/*.md
git add /raid/shared/lineages-website/global_report_*.md
git add /raid/shared/lineages-website/_data/lineages.metadata.csv
git add /raid/shared/lineages-website/_data/lineage_data.json
git add /raid/shared/lineages-website/_data/grinch_data.json
git add /raid/shared/lineages-website/assets/images/*.svg

git commit -m "updating new variant report $TODAY"
git push

