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
cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/report/global_report_B.1.617.2.md ~/git/lineages-website/global_report_B.1.617.2.md
cp /localdisk/home/shared/raccoon-dog/"$TODAY"_website/report/global_report_B.1.1.529.md ~/git/lineages-website/global_report_B.1.1.529.md

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

PANGO=/localdisk/home/shared/raccoon-dog/"$TODAY"_gisaid/publish/pangolin/*.cache.csv
echo "Using pango file $PANGO"
conda activate datapipe
pangoLEARN_version=$(pangolin --all-versions | grep "pango-designation used by pangoLEARN/Usher" | cut -f5 -d" ")

cd ~/git/pangolin-assignment
current_pangoLEARN_version=$(cat pangolin_assignment/__init__.py | grep "__version__" | cut -f3 -d" ")
major_version=${current_pangoLEARN_version:1:7}
minor_version=${current_pangoLEARN_version:9:1}
echo $pangoLEARN_version
echo $current_pangoLEARN_version
echo $major_version
echo $minor_version

mv pango_assignment.cache.*.csv old.csv

if [[ $(wc -l <$PANGO) -ge 4000000 ]]
then
  cp $PANGO pango_assignment.cache."$TODAY".csv
  echo "Replace file with new assignments"
  if [[ $pangoLEARN_version == $current_pangoLEARN_version ]]
  then
    minor_version=$((minor_version + 1))
  else
    minor_version=0
    major_version=$pangoLEARN_version
  fi
else
  head -n1 $PANGO > pango_assignment.cache."$TODAY".csv
  cat $PANGO old.csv | sort -u | tail -n+1 >> pango_assignment.cache."$TODAY".csv
  echo "Add to assignments"
fi
gzip -c ~/git/pangolin-assignment/pango_assignment.cache."$TODAY".csv > ~/git/pangolin-assignment/pangolin_assignment/pango_assignment.cache.csv.gz
git add pangolin_assignment/pango_assignment.cache.csv.gz
echo '_program = "pangolin-assignment"' > ~/git/pangolin-assignment/pangolin_assignment/__init__.py
echo "__version__ = \"$major_version.$minor_version\" >> ~/git/pangolin-assignment/pangolin_assignment/__init__.py
echo "__date__ = \"$TODAY\"" >> ~/git/pangolin-assignment/pangolin_assignment/__init__.py
git add pangolin_assignment/__init__.py
git commit -m "update lineage assignment cache $TODAY"
git push

echo "Finished!"
