#!/usr/bin/env python3
import pkg_resources
from grinch.utils.log_colours import green,cyan,red
import sys
import os

from grinch.utils import grinchfunks as gfunk

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


def get_report_snakefile(thisdir):
    snakefile = os.path.join(thisdir, 'scripts','render_report.smk')
    if not os.path.exists(snakefile):
        sys.stderr.write(cyan(f'Error: cannot find Snakefile at {snakefile}\n Check installation\n'))
        sys.exit(-1)
    return snakefile


def check_install(config):
    resources = [
        {"key":"reference",
        "directory":"data",
        "filename":"reference.fasta"},
        {"key":"genbank_ref",
        "directory":"data",
        "filename":"WH04.gb"},
        {"key":"world_map_file",
        "directory":"data",
        "filename":"world_map.json"},
        {"key":"omitted",
        "directory":"data",
        "filename":"omitted.csv"},
        {"key":"outgroups",
        "directory":"data",
        "filename":"outgroups.csv"},
        {"key":"continent_file",
        "directory":"data",
        "filename":"continent_mapping.csv"},
        {"key":"lineage_info",
        "directory":"data",
        "filename":"lineage_info.json"},
    ]
    for resource in resources:
        package_data_check(resource["filename"],resource["directory"],resource["key"],config)

# config={}
# check_install()

def check_access(json,username,password,url,filename,cwd,config):
    if json:
        json = os.path.join(cwd,json)
    gfunk.add_arg_to_config("json",json,config)
    gfunk.add_arg_to_config("username",username,config)
    gfunk.add_arg_to_config("password",password,config)
    gfunk.add_arg_to_config("url",url,config)
    gfunk.add_arg_to_config("filename",filename,config)

    if not config["json"] and config["analysis"]=="full":
        if not config["username"] or not config["password"] or not config["url"] or not config["filename"]:
            sys.stderr.write(cyan(f'Error: please either provide a json file, a metadata file (with analysis option `report_only`) or the correct gisaid access information.\n'))
            sys.exit(-1)

    if not config["metadata"] and config["analysis"]=="report_only":
        sys.stderr.write(cyan(f'Error: please provide a metadata file (with analysis option `report_only`) or the correct gisaid access information, or a json file of gisaid data.\n'))
        sys.exit(-1)
    elif config["metadata"]:
        config["metadata"] = os.path.join(cwd,config["metadata"])
        if not os.path.exists(config["metadata"]):
            sys.stderr.write(cyan(f'Error: metadata input file not found ') + f"{config['metadata']}\n")
            sys.exit(-1)

    
