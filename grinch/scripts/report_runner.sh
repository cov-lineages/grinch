#!/bin/bash

python setup.py install

snakemake --snakefile /Users/s1680070/repositories/grinch/grinch/scripts/test.smk --configfile /Users/s1680070/repositories/grinch/grinch/data/config.yaml --cores 1 --forceall --nolock

cp /Users/s1680070/repositories/grinch/report/global_report_* /Users/s1680070/repositories/lineages-website && cp /Users/s1680070/repositories/grinch/report/grinch_data.json /Users/s1680070/repositories/lineages-website/_data && cp /Users/s1680070/repositories/grinch/figures/*.svg /Users/s1680070/repositories/lineages-website/assets/images

cd /Users/s1680070/repositories/lineages-website

git add /Users/s1680070/repositories/lineages-website/assets/images/*.svg

git add /Users/s1680070/repositories/lineages-website/_data/grinch_data.json 

#git commit -m "updating grinch report"

#git push
