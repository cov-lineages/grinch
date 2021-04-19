#!/usr/bin/env python3
import os
import argparse
import collections
from grinch import __version__
from datetime import date
from datetime import datetime
import pangoLEARN
import pangolin
import pkg_resources

import json
import csv
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Report generator script")
    parser.add_argument("--metadata", required=True, help="metadata file", dest="metadata")
    parser.add_argument("--data", help="output data file", dest="data")
    parser.add_argument("--outdir", help="output dir", dest="outdir")
    parser.add_argument("--variants-info", help="variants_info",dest="variants_info")
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

def get_conversion_dict():
    conversion_dict = {}
    conversion_dict["United_States"] = "United States of America"
    conversion_dict["USA"] = "United States of America"
    conversion_dict["Viet_Nam"] = "Vietnam"
    conversion_dict["Macedonia"] = "North_Macedonia"
    conversion_dict["Serbia"] = "Republic of Serbia"
    conversion_dict["Côte_d’Ivoire"] = "Ivory Coast"
    conversion_dict["Cote_dIvoire"] = "Ivory Coast"
    conversion_dict["CÔTE_D'IVOIRE"] = "Ivory Coast"
    conversion_dict["Czech_Repubic"] = "Czech Republic"
    conversion_dict["UK"] = "United Kingdom"
    conversion_dict["Timor-Leste"] = "East Timor"
    conversion_dict["DRC"] = "Democratic Republic of the Congo"
    conversion_dict["Saint_Barthélemy"] = "Saint-Barthélemy"
    conversion_dict["Saint_Martin"] = "Saint-Martin"
    conversion_dict["Curacao"] = "Curaçao"
    conversion_dict["St. Lucia"] = "Saint Lucia"
    conversion_dict["Gaborone"] = "Botswana"
    return conversion_dict

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
    
def make_summary_data(metadata,import_data,raw_data,lineages_of_concern):
    # add lineages and sub lineages into a dict with verity's summary information about each lineage

    summary_dict = collections.defaultdict(dict)

    for lineage in lineages_of_concern:
        summary_dict[lineage] = {"Lineage":lineage,
                                "Country count":0,
                                "Countries":collections.Counter(),
                                "Earliest date": "",
                                "Count":0,
                                "Date":collections.Counter(),
                                "Travel history":collections.Counter(),
                                "import_report":import_data[lineage],
                                "aggregate_data":raw_data[lineage]
                                }

    conversion_dict = get_conversion_dict()

    with open(metadata,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["sample_date"]:
                country = row["country"]

                d = date.fromisoformat(row["sample_date"])
                cut_off = datetime.strptime("2020-09-01", "%Y-%m-%d").date()
                travel_history = row["travel_history"]
                lineage = row["lineage"]
                if d < cut_off: 
                    pass
                else:
                    if lineage != "" and lineage in lineages_of_concern:

                        if country == "Caribbean":
                            country = row["sequence_name"].split("/")[0]
                        
                        if country in conversion_dict:
                            country = conversion_dict[country]
                        country = country.replace("_"," ")
                        
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


def make_constellation_data(metadata,variant_info,lineages_of_concern):
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
                if constellation != "" and constellation in lineages_of_concern:
                    
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
    lineage_info = pkg_resources.resource_filename('grinch', f'data/lineage_info.json')
    with open(lineage_info,"r") as f:
        lineage_info = json.load(f)

    lineages_of_concern = []
    import_data = {}
    for lineage in lineage_info:
        lineages_of_concern.append(lineage)
        lin_data = lineage_info[lineage]

        if lin_data["import_data"] == "Y":
            import_report_file = pkg_resources.resource_filename('grinch', f'data/local_imported_{lineage}.csv')
            lineage_import_data = parse_import_data(import_report_file)
            import_data[lineage] = lineage_import_data
        else:
            import_data[lineage] = "NA"
        
        # write lineage page site
        with open(f'{args.outdir}/report/global_report_{lineage}.md','w') as fw:
            fw.write('---\n')
            fw.write(f'layout: global_report_page\n')
            fw.write(f'lineage: "{lineage}"\n')
            fw.write(f'version: "{__version__}"\n')
            fw.write(f'v: "{pangolin.__version__}"\n')
            fw.write(f'pv: "{pangoLEARN.__version__}"\n')
            now = datetime.now()
            date_time = now.strftime("%Y-%m-%d, %H:%M GMT")
            fw.write(f'timestamp: "{date_time}"\n')
            fw.write(f'today: "{date.today()}"\n')
            for i in lin_data:
                if i =='snps':
                    snps = lin_data[i]
                    snps = snps.replace(';','<br> ')
                    fw.write(f'snps: "{snps}"\n')
                else:
                    fw.write(f'{i}: "{lin_data[i]}"\n')
            fw.write('---\n')

    # raw data
    raw_data = {}
    for lineage in lineages_of_concern:
        raw_data_file = os.path.join(args.outdir,"figures",f"{lineage}_raw_data.csv")
        lineage_raw_data = parse_raw_data(raw_data_file)
        raw_data[lineage] = lineage_raw_data
    
    summary_data = make_summary_data(args.metadata,import_data,raw_data,lineages_of_concern)

    with open(args.data,"w") as fw:
        json.dump(summary_data, fw, indent=4)

if __name__ == "__main__":
    make_report()
