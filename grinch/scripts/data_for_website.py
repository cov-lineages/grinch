#!/usr/bin/env python3
import os
import argparse
import collections
from grinch import __version__
from datetime import date
import pangoLEARN
import pangolin

import json
import csv
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Report generator script")
    parser.add_argument("--metadata", required=True, help="metadata file", dest="metadata")
    parser.add_argument("--data", help="output data file", dest="data")
    parser.add_argument("--outdir", help="output dir", dest="outdir")
    parser.add_argument("--lineage-info", help="lineage_info",dest="lineage_info")
    parser.add_argument("--variants-info", help="variants_info",dest="variants_info")
    parser.add_argument("--time", help="timestamp", dest="time")
    parser.add_argument("--import-report-b117", help="import report", dest="import_report_b117")
    parser.add_argument("--import-report-b1351", help="import report", dest="import_report_b1351")
    parser.add_argument("--import-report-p1", help="import report", dest="import_report_p1")
    parser.add_argument("--raw-data-b117", help="raw data", dest="raw_data_b117")
    parser.add_argument("--raw-data-b1351", help="raw data", dest="raw_data_b1351")
    parser.add_argument("--raw-data-p1", help="raw data", dest="raw_data_p1")
    return parser.parse_args()

def parse_import_data(import_report):
    import_data = []
    with open(import_report, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_data = {"Country": row["Country"],
                        "Earliest report": row["earliest_report"],
                        "Date local transmission": row["date_local"],
                        "Local transmission": row["imported_local"],
                        "Method of surveillance": row["method_surveillance"],
                        "Source": row["Source"]
                        }
            import_data.append(row_data)
    return import_data

def parse_raw_data(raw_data_csv):
    raw_data = []
    with open(raw_data_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_data = {"Country": row["Country"],
                        "Earliest sequence": row["earliest_date"],
                        "Number of variant sequences": row["number_of_sequences"],
                        "Total sequences since first variant sequence": row["Total sequences since first report"]
                        }
            raw_data.append(row_data)
    return raw_data
    
def make_summary_data(metadata,import_data,raw_data):
    # add lineages and sub lineages into a dict with verity's summary information about each lineage

    summary_dict = collections.defaultdict(dict)

    for lineage in ["B.1.351","B.1.1.7","P.1"]:
        summary_dict[lineage] = {"Lineage":lineage,
                                "Country count":0,
                                "Countries":collections.Counter(),
                                "Earliest date": "",
                                "Count":0,
                                "Date":collections.Counter(),
                                "Travel history":collections.Counter(),
                                "Likely origin":"",
                                "import_report":import_data[lineage],
                                "aggregate_data":raw_data[lineage]
                                }
    
    summary_dict["B.1.1.7"]["Likely origin"] = "United Kingdom"
    summary_dict["B.1.351"]["Likely origin"] = "South Africa"
    summary_dict["P.1"]["Likely origin"] = "Brazil"
    # compile data for json
    with open(metadata,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["sample_date"]:
                country = row["country"]
            
                d = date.fromisoformat(row["sample_date"])

                travel_history = row["travel_history"]
                lineage = row["lineage"]

                if lineage != "" and lineage in ["B.1.1.7","B.1.351","P.1"]:
                    
                    summary_dict[lineage]["Countries"][country]+=1
                    
                    if summary_dict[lineage]["Earliest date"]:
                    
                        if d < summary_dict[lineage]["Earliest date"]:
                            summary_dict[lineage]["Earliest date"] = d
                    else:
                        summary_dict[lineage]["Earliest date"] = d
                    
                    summary_dict[lineage]["Date"][str(d)] +=1

                    summary_dict[lineage]["Count"] +=1 

                    if travel_history:
                        summary_dict[lineage]["Travel history"][travel_history]+=1

    for lineage in summary_dict:
        fig_count = 0
        travel = summary_dict[lineage]["Travel history"]
        travel_info = ""
        for k in travel:
            travel_info += f"{travel[k]} {k}; "
        travel_info = travel_info.rstrip(";")
        summary_dict[lineage]["Travel history"] = travel_info

        countries = summary_dict[lineage]["Countries"]
        summary_dict[lineage]["Country count"] = len(countries)
        country_info = ""
        total = sum(countries.values())
        for k in countries.most_common(200):
            
            pcent = round((100*k[1])/total, 0)
            country_info += f"{k[0]} {k[1]}, "
        country_info = country_info.rstrip(", ")
        summary_dict[lineage]["Countries"] = country_info
        
        summary_dict[lineage]["Earliest date"] = str(summary_dict[lineage]["Earliest date"])

        date_objects = []
        for d in summary_dict[lineage]["Date"]:

            date_objects.append({"date":d,"count":summary_dict[lineage]["Date"][d]})
        summary_dict[lineage]["Date"] = date_objects

    return summary_dict


def make_constellation_data(metadata,variant_info):
    # add constellations into a dict 

    summary_dict = collections.defaultdict(dict)

    for constellation in ["RBD"]:
        summary_dict[constellation] = {"constellation":constellation,
                                "Country count":0,
                                "Countries":collections.Counter(),
                                "Earliest date": "",
                                "Count":0,
                                "lineages":collections.Counter(),
                                "Date":collections.Counter()
                                }

    # compile data for json
    with open(metadata,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["sample_date"]:
                country = row["country"]
            
                d = date.fromisoformat(row["sample_date"])
                constellation = row["constellation"].split()
                if constellation != "" and constellation in ["B.1.1.7","B.1.351","P.1"]:
                    
                    summary_dict[lineage]["Countries"][country]+=1
                    
                    if summary_dict[lineage]["Earliest date"]:
                    
                        if d < summary_dict[lineage]["Earliest date"]:
                            summary_dict[lineage]["Earliest date"] = d
                    else:
                        summary_dict[lineage]["Earliest date"] = d
                    
                    summary_dict[lineage]["Date"][str(d)] +=1

                    summary_dict[lineage]["Count"] +=1 

                    if travel_history:
                        summary_dict[lineage]["Travel history"][travel_history]+=1

    for lineage in summary_dict:
        fig_count = 0
        travel = summary_dict[lineage]["Travel history"]
        travel_info = ""
        for k in travel:
            travel_info += f"{travel[k]} {k}; "
        travel_info = travel_info.rstrip(";")
        summary_dict[lineage]["Travel history"] = travel_info

        countries = summary_dict[lineage]["Countries"]
        summary_dict[lineage]["Country count"] = len(countries)
        country_info = ""
        total = sum(countries.values())
        for k in countries.most_common(50):
            
            pcent = round((100*k[1])/total, 0)
            country_info += f"{k[0]} {k[1]}, "
        country_info = country_info.rstrip(", ")
        summary_dict[lineage]["Countries"] = country_info
        
        summary_dict[lineage]["Earliest date"] = str(summary_dict[lineage]["Earliest date"])

        date_objects = []
        for d in summary_dict[lineage]["Date"]:

            date_objects.append({"date":d,"count":summary_dict[lineage]["Date"][d]})
        summary_dict[lineage]["Date"] = date_objects

    return summary_dict

def make_report():

    args = parse_args()

    # loading constant info about lineages
    with open(args.lineage_info,"r") as f:
        lineage_info = json.load(f)

    for lineage in ["B.1.351","B.1.1.7","P.1"]:

        lin_data = lineage_info[lineage]
        
        # write lineage page site
        with open(f'{args.outdir}/report/global_report_{lineage}.md','w') as fw:
            fw.write('---\n')
            fw.write(f'layout: global_report_page\n')
            fw.write(f'lineage: "{lineage}"\n')
            fw.write(f'version: "{__version__}"\n')
            fw.write(f'v: "{pangolin.__version__}"\n')
            fw.write(f'pv: "{pangoLEARN.__version__}"\n')
            fw.write(f'timestamp: "{args.time}"\n')
            fw.write(f'today: "{date.today()}"\n')
            for i in lin_data:
                if i =='snps':
                    snps = lin_data[i]
                    snps = snps.replace(';','<br> ')
                    fw.write(f'snps: "{snps}"\n')
                else:
                    fw.write(f'{i}: "{lin_data[i]}"\n')
            fw.write('---\n')

    # import report info
    import_data_b117 = parse_import_data(args.import_report_b117)
    import_data_b1351 = parse_import_data(args.import_report_b1351)
    import_data_p1 = parse_import_data(args.import_report_p1)
    import_data = {
                    "B.1.1.7": import_data_b117,
                    "B.1.351": import_data_b1351,
                    "P.1": import_data_p1
                    }

    # raw data
    args.raw_data_b1351
    raw_data_b117 = parse_raw_data(args.raw_data_b117)
    raw_data_b1351 = parse_raw_data(args.raw_data_b1351)
    raw_data_p1 = parse_raw_data(args.raw_data_p1)
    raw_data = {
                "B.1.1.7": raw_data_b117,
                "B.1.351": raw_data_b1351,
                "P.1": raw_data_p1
                }

    summary_data = make_summary_data(args.metadata,import_data,raw_data)

    with open(args.data,"w") as fw:
        json.dump(summary_data, fw, indent=4)

if __name__ == "__main__":
    make_report()
