#!/usr/bin/env python3


import grinch.utils.custom_logger as custom_logger
import grinch.utils.log_handler_handle as lh
from grinch.utils import grinchfunks

import os
import argparse
import csv 
import sys
from Bio import SeqIO
from datetime import datetime 
from datetime import date

import tempfile
import pkg_resources
import yaml

import sys
import math

def set_up_verbosity(config):
    if config["verbose"]:
        config["quiet"] = False
        config["log_api"] = ""
        config["log_string"] = ""
    else:
        config["quiet"] = True
        logger = custom_logger.Logger()
        config["log_api"] = logger.log_handler

        lh_path = os.path.realpath(lh.__file__)
        config["log_string"] = f"--quiet --log-handler-script {lh_path} "

def make_chunks(fasta_in, outdir):
    pref = fasta_in.split(".")[0]
    pref = pref.split("/")[-1]
    pref = outdir +'/' + pref
    record_counter = 0
    with open(fasta_in, "r") as f:
        for record in SeqIO.parse(f, "fasta"):
            record_counter += 1

    n_chunks = math.ceil(record_counter / 10000)

    file_handles = [open(pref + "_" + str(i) + ".fasta", "w") for i in range(n_chunks)]

    chunk_counter = 0
    record_counter = 0
    with open(fasta_in, "r") as f:
        for record in SeqIO.parse(f, "fasta"):
            file_handles[chunk_counter].write(">" + record.id + "\n")
            file_handles[chunk_counter].write(str(record.seq) + "\n")

            record_counter += 1
            if record_counter % 10000 == 0:
                chunk_counter += 1

    for fh in file_handles:
        fh.close()

def get_defaults():
    default_dict = {"threads":1,
                    "config":False,
                    "verbose":False,
                    "analysis":"full",
                    "data_column":"sequence_name",
                    "output_prefix":"global_report",
                    "summary_fields":"node_number,most_recent_tip,tip_count,admin0_count,admin1_count",
                    "cluster_fields":"node_number,day_range,tip_count,uk_tip_count,uk_chain_count,identical_count",
                    "no_temp":False,
                    "threads":5,
                    "outdir":os.getcwd(),
                    "force":True
                    }
    return default_dict

def get_snakefile(thisdir):
    snakefile = os.path.join(thisdir, 'scripts','grinch_report.smk')
    if not os.path.exists(snakefile):
        sys.stderr.write(cyan(f'Error: cannot find Snakefile at {snakefile}\n Check installation\n'))
        sys.exit(-1)
    return snakefile

def get_temp_dir(tempdir_arg,no_temp_arg, cwd,config):
    tempdir = ''
    outdir = config["outdir"]
    if no_temp_arg:
        print(green(f"--no-temp:") + f" All intermediate files will be written to {outdir}")
        tempdir = outdir
        config["no_temp"] = no_temp_arg
    elif config["no_temp"]:
        print(green(f"--no-temp:") + f" All intermediate files will be written to {outdir}")
        tempdir = outdir
    elif tempdir_arg:
        expanded_path = os.path.expanduser(tempdir_arg)
        to_be_dir = os.path.join(cwd,expanded_path)
        if not os.path.exists(to_be_dir):
            os.mkdir(to_be_dir)
        temporary_directory = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=to_be_dir)
        tempdir = temporary_directory.name

    elif "tempdir" in config:
        expanded_path = os.path.expanduser(config["tempdir"])
        to_be_dir = os.path.join(cwd,expanded_path)
        if not os.path.exists(to_be_dir):
            os.mkdir(to_be_dir)
        temporary_directory = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=to_be_dir)
        tempdir = temporary_directory.name

    else:
        temporary_directory = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=None)
        tempdir = temporary_directory.name
    
    config["tempdir"] = tempdir 
    return tempdir
    
def parse_yaml_file(configfile,config):
    with open(configfile,"r") as f:
        input_config = yaml.load(f, Loader=yaml.FullLoader)
        for key in input_config:
            snakecase_key = key.replace("-","_")
            config[snakecase_key] = input_config[key]

def add_arg_to_config(key,arg,config):
    if arg:
        config[key] = arg

    pkg_resources.resource_filename('grinch', 'data/omitted.csv')
def colour(text, text_colour):
    bold_text = 'bold' in text_colour
    text_colour = text_colour.replace('bold', '')
    underline_text = 'underline' in text_colour
    text_colour = text_colour.replace('underline', '')
    text_colour = text_colour.replace('_', '')
    text_colour = text_colour.replace(' ', '')
    text_colour = text_colour.lower()
    if 'red' in text_colour:
        coloured_text = RED
    elif 'green' in text_colour:
        coloured_text = GREEN
    elif 'yellow' in text_colour:
        coloured_text = YELLOW
    elif 'dim' in text_colour:
        coloured_text = DIM
    elif 'cyan' in text_colour:
        coloured_text = 'cyan'
    else:
        coloured_text = ''
    if bold_text:
        coloured_text += BOLD
    if underline_text:
        coloured_text += UNDERLINE
    if not coloured_text:
        return text
    coloured_text += text + END_FORMATTING
    return coloured_text

def red(text):
    return RED + text + END_FORMATTING

def cyan(text):
    return CYAN + text + END_FORMATTING

def green(text):
    return GREEN + text + END_FORMATTING

def yellow(text):
    return YELLOW + text + END_FORMATTING

def bold_underline(text):
    return BOLD + UNDERLINE + text + END_FORMATTING
