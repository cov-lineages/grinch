#!/usr/bin/env python3
from grinch import __version__

import setuptools
import argparse
import os.path
import snakemake
import sys
import tempfile
import csv
import os
import yaml
from datetime import datetime
from datetime import date
from Bio import SeqIO
import pkg_resources
from . import _program
from grinch.utils.log_colours import green,cyan,red


from grinch.utils import dependency_checks
from grinch.utils import data_install_checks

import grinch.utils.custom_logger as custom_logger
from grinch.utils import grinchfunks as gfunk

thisdir = os.path.abspath(os.path.dirname(__file__))


def main(sysargs = sys.argv[1:]):

    parser = argparse.ArgumentParser(prog = _program, 
    usage='''grinch -i <config.yaml> [options]''')

    io_group = parser.add_argument_group('input output options')
    io_group.add_argument('-a',"--analysis",action="store",help="Analysis entry point: `full` or `report_only`. Default: `full`",dest="analysis")
    io_group.add_argument('-i',"--config", action="store",help="Input config file", dest="config")
    io_group.add_argument('-j',"--json", action="store",help="GISAID JSON data",dest="json")
    io_group.add_argument('-m',"--metadata", action="store",help="Input metadata",dest="metadata")

    io_group.add_argument('--outdir', action="store",help="Output directory. Default: current working directory")
    io_group.add_argument('-o','--output-prefix', action="store",help="Output prefix. Default: grinch",dest="output_prefix")

    io_group.add_argument("--alias",action="store",help="Alias JSON file")
    io_group.add_argument('--filename', action="store",help="File to access.")
    io_group.add_argument('--url', action="store",help="URL to access.")
    io_group.add_argument('--username', action="store",help="Username for access.")
    io_group.add_argument('--password', action="store",help="Password for access.")

    misc_group = parser.add_argument_group('misc options')
    misc_group.add_argument('--tempdir',action="store",help="Specify where you want the temporary stuff to go Default: $TMPDIR")
    misc_group.add_argument("--no-temp",action="store_true",help="Output all intermediate files")
    misc_group.add_argument("--verbose",action="store_true",help="Print lots of stuff to screen")
    misc_group.add_argument("--no-force",action="store_true",help="Dont force run rules",dest="no_force")
    misc_group.add_argument('-t','--threads', action='store',dest="threads",type=int,help="Number of threads")
    misc_group.add_argument("-v","--version", action='version', version=f"grinch {__version__}")
    
    """
    Exit with help menu if no args supplied
    """
    if len(sysargs)<1: 
        parser.print_help()
        sys.exit(-1)
    else:
        args = parser.parse_args(sysargs)
    
    """
    Initialising dicts
    """

    # get the default values from grinchfunks
    config = gfunk.get_defaults()

    data_install_checks.check_install(config)
    
    dependency_checks.set_up_verbosity(config)

    """
    Valid inputs are config.yaml/config.yml
    
    """
    # find config file
    if args.config:
        gfunk.add_arg_to_config("config",args.config,config)

    # if a yaml file is detected, add everything in it to the config dict
    if config["config"]:
        gfunk.parse_yaml_file(config["config"], config)

    gfunk.add_arg_to_config("analysis",args.analysis,config)

    gfunk.add_arg_to_config("metadata",args.metadata,config)

    if config["analysis"] not in ["full","report_only"]:
        sys.stderr.write(cyan(f'Error: please speficify either `full` or `report_only` for analysis option.\n'))
        sys.exit(-1)
    elif config["analysis"] == "full":
        snakefile = data_install_checks.get_snakefile(thisdir)
    else:
        if not config["metadata"]:
            sys.stderr.write(cyan(f'Error: please provide `metadata` for `report_only` grinch.\n'))
            sys.exit(-1)
        snakefile = data_install_checks.get_report_snakefile(thisdir)

    gfunk.add_arg_to_config("alias",args.alias,config)

    config["flight_data_path"] = os.path.join(thisdir,"data","flights")
    config["import_report_path"] = os.path.join(thisdir,"data")

    """
    Output directory 
    """
    # default output dir
    gfunk.add_arg_to_config("outdir",args.outdir,config)
    config["outdir"]=os.path.abspath(config["outdir"])
    if not os.path.exists(config["outdir"]):
        os.mkdir(config["outdir"])
    figdir  = os.path.join(config["outdir"], "figures")
    if not os.path.exists(figdir):
        os.mkdir(figdir)
    config['figdir'] = figdir

    """
    Get tempdir 
    """
    
    # specifying temp directory, outdir if no_temp (tempdir becomes working dir)
    tempdir = gfunk.get_temp_dir(args.tempdir, args.no_temp,os.getcwd(),config)
    config["tempdir"] = tempdir

    config["lineages_of_concern"] = ["B.1.1.7","B.1.351","P.1","B.1.617.2","B.1.1.529"]

    config["snps"] = gfunk.get_snps()
    """
    Miscellaneous options parsing

    """
    # don't run in quiet mode if verbose specified
    gfunk.add_arg_to_config("verbose",args.verbose,config)
    gfunk.set_up_verbosity(config)

    if args.no_force:
        force_option = False
    else:
        force_option = True
    
    config["force"] = force_option

    gfunk.add_arg_to_config("threads",args.threads,config)
    
    try:
        config["threads"]= int(config["threads"])
    except:
        sys.stderr.write(gfunk.cyan('Error: Please specifiy an integer for variable `threads`.\n'))
        sys.exit(-1)
    threads = config["threads"]

    data_install_checks.check_access(args.json,args.username,args.password,args.url,args.filename,os.getcwd(),config)

    if config["json"]:
        pass
    elif config["analysis"]=="full":
        fn = config["filename"]
        fn_unzipped = ".".join(fn.split(".")[:-1])
        if os.path.exists(fn):
            os.system(f"rm {fn}")
        if os.path.exists(fn_unzipped):
            os.system(f"rm {fn_unzipped}")
        os.system(f"wget --password {config['password']} "
                    f"--user {config['username']} {config['url']} "
                    "&& "
                    f"bzip2 -d {fn} ")
        config["json"] = os.path.join(os.getcwd(),fn_unzipped)

    elif config["analysis"]=="report_only":
        if not config["metadata"]:
            sys.stderr.write(gfunk.cyan('Error: provide a metadata file.\n'))
            sys.exit(-1)

    # config["timestamp"] = gfunk.get_timestamp()
    
    

    if config['verbose']:
        print(green("\n**** CONFIG ****"))
        for k in sorted(config):
            print(green(k), config[k])

        status = snakemake.snakemake(snakefile, printshellcmds=True, forceall=True, force_incomplete=True,
                                        workdir=tempdir,config=config, cores=threads,lock=False
                                        )
    else:
        logger = custom_logger.Logger()
        status = snakemake.snakemake(snakefile, printshellcmds=False, forceall=True,force_incomplete=True,workdir=tempdir,
                                    config=config, cores=threads,lock=False,quiet=True,log_handler=config["log_api"]
                                    )

    if status: # translate "success" into shell exit code of 0
       return 0

    return 1

if __name__ == '__main__':
    main()
