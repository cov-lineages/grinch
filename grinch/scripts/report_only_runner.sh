#!/usr/bin/bash

if [ -z "$1" ]; then
  TODAY=`date +'%Y-%m-%d'`
else
  TODAY=$1
fi

if [ -z "$2" ]; then
    GIT_REPO_DIR="/localdisk/home/$(whoami)/git"
else
    GIT_REPO_DIR=$2
fi

source /localdisk/home/shared/scripts/.keys

echo "TODAY: $TODAY"
echo "GIT_REPO_DIR: $GIT_REPO_DIR"
echo "SHARED_RACCOON_DIR: $SHARED_RACCOON_DIR"

eval "$(conda shell.bash hook)"
conda activate /localdisk/home/shared/miniconda3/envs/grinch

cd $GIT_REPO_DIR/pango-designation && git pull #gets any updates to the reports in the data directory

cd $GIT_REPO_DIR/grinch && git pull #gets any updates to the reports in the data directory
pip install .

echo "RUN GRINCH for date $TODAY"
METADATA=$SHARED_RACCOON_DIR/"$TODAY"_gisaid/publish/gisaid/gisaid_"$TODAY"_all_metadata.csv
echo "Using metadata $METADATA"
which grinch
echo $PWD
outdir=$SHARED_RACCOON_DIR/"$TODAY"_website
grinch -t 10 -m $METADATA --outdir $outdir --output-prefix global_report -a report_only --alias $GIT_REPO_DIR/pango-designation/pango_designation/alias_key.json --verbose --no-temp

echo "Update website"
cd $GIT_REPO_DIR/lineages-website && git pull

python $GIT_REPO_DIR/grinch/grinch/scripts/update_website.py \
  --website-dir $GIT_REPO_DIR/lineages-website \
  -m $METADATA \
  -d $GIT_REPO_DIR/pango-designation/lineages.csv \
  -n $GIT_REPO_DIR/pango-designation/lineage_notes.txt \
  -o $GIT_REPO_DIR/lineages-website/_data/lineage_data.json \
  -a $GIT_REPO_DIR/pango-designation/pango_designation/alias_key.json

echo "Place output files"
cp $outdir/report/global_report_*.md $GIT_REPO_DIR/lineages-website/
cp $outdir/report/grinch_data.json $GIT_REPO_DIR/lineages-website/_data/grinch_data.json
cp $outdir/figures/*.svg $GIT_REPO_DIR/lineages-website/assets/images/

git add $GIT_REPO_DIR/lineages-website/lineages.md
git add $GIT_REPO_DIR/lineages-website/lineages/*.md
git add --all $GIT_REPO_DIR/lineages-website/lineages/*/*.md
git add $GIT_REPO_DIR/lineages-website/global_report_*.md
git add $GIT_REPO_DIR/lineages-website/_data/lineage_data.json
git add $GIT_REPO_DIR/lineages-website/_data/lineage_data.full.json
git add $GIT_REPO_DIR/lineages-website/_data/grinch_data.json
git add $GIT_REPO_DIR/lineages-website/assets/images/*.svg
git add $GIT_REPO_DIR/lineages-website/_data/lineages.yml
git add $GIT_REPO_DIR/lineages-website/data/lineages.yml

git commit -m "updating website $TODAY"
git push

###
#PANGO=/localdisk/home/shared/raccoon-dog/"$TODAY"_gisaid/publish/pangolin/*.cache.csv
#echo "Using pango file $PANGO"
#conda activate datapipe
#pangoLEARN_version=$(pangolin --all-versions | grep "pango-designation used by pangoLEARN/Usher" | cut -f5 -d" ")

#cd ~/git/pangolin-assignment
#current_pangoLEARN_version=$(cat pangolin_assignment/__init__.py | grep "__version__" | cut -f3 -d" ")
#major_version=${current_pangoLEARN_version:1:7}
#minor_version=${current_pangoLEARN_version:9:1}
#echo $pangoLEARN_version
#echo $current_pangoLEARN_version
#echo $major_version
#echo $minor_version

#mv pango_assignment.cache.*.csv old.csv

#if [[ $(wc -l <$PANGO) -ge 4000000 ]]
#then
#  cp $PANGO pango_assignment.cache."$TODAY".csv
#  echo "Replace file with new assignments"
#  if [[ $pangoLEARN_version == $current_pangoLEARN_version ]]
#  then
#    minor_version=$((minor_version + 1))
#  else
#    minor_version=0
#    major_version=$pangoLEARN_version
#  fi
#else
#  head -n1 $PANGO > pango_assignment.cache."$TODAY".csv
#  cat $PANGO old.csv | sort -u | tail -n+1 >> pango_assignment.cache."$TODAY".csv
#  echo "Add to assignments"
#fi
#gzip -c ~/git/pangolin-assignment/pango_assignment.cache."$TODAY".csv > ~/git/pangolin-assignment/pangolin_assignment/pango_assignment.cache.csv.gz
#git add pangolin_assignment/pango_assignment.cache.csv.gz
#echo '_program = "pangolin-assignment"' > ~/git/pangolin-assignment/pangolin_assignment/__init__.py
#echo "__version__ = \"$major_version.$minor_version\"" >> ~/git/pangolin-assignment/pangolin_assignment/__init__.py
#echo "__date__ = \"$TODAY\"" >> ~/git/pangolin-assignment/pangolin_assignment/__init__.py
#git add pangolin_assignment/__init__.py
#git commit -m "update lineage assignment cache $TODAY"
#git push

echo "Finished!"
