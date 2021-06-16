#!/usr/bin/env python3
import pkg_resources
from grinch.utils.log_colours import green,cyan,red
import sys
import os


def package_data_check(filename,directory,key,config):
    try:
        package_datafile = os.path.join(directory,filename)
        data = pkg_resources.resource_filename('grinch', package_datafile)
        config[key] = data
    except:
        sys.stderr.write(cyan(f'Error: Missing package data.')+f'\n\t- {filename}\nPlease install the latest grinch version with `grinch --update`.\n')
        sys.exit(-1)

def get_snakefile(thisdir):
    snakefile = os.path.join(thisdir, 'scripts','grinch_report.smk')
    if not os.path.exists(snakefile):
        sys.stderr.write(cyan(f'Error: cannot find Snakefile at {snakefile}\n Check installation\n'))
        sys.exit(-1)
    return snakefile

def check_install(config):
    resources = [
        {"key":"reference_fasta",
        "directory":"data",
        "filename":"reference.fasta"},
        {"key":"genbank_ref",
        "directory":"data",
        "filename":"WH04.gb"},
        {"key":"world_map",
        "directory":"data",
        "filename":"world_map.json"},
        {"key":"omitted",
        "directory":"data",
        "filename":"omitted.csv"},
        {"key":"outgroups",
        "directory":"data",
        "filename":"outgroups.csv"}
    ]
    for resource in resources:
        package_data_check(resource["filename"],resource["directory"],resource["key"],config)

# config={}
# check_install()
