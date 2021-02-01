#!/usr/bin/env python3
import csv
import json
import os
import argparse
import collections
from datetime import date
import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Update lineage web pages for cov-lineages.org')

    parser.add_argument("--website-dir", action="store", type=str, dest="website_dir")
    parser.add_argument('-m',"--metadata", action="store",type=str, dest="metadata")
    parser.add_argument('-n',"--lineage-notes", action="store",type=str, dest="lineage_notes")
    parser.add_argument("-o","--outfile",action="store",type=str, dest="json_outfile")
    return parser.parse_args()

def get_description_dict(description_file):
    lineages = {}
    with open(description_file,"r") as f:
        for l in f:
            l = l.rstrip("\n")
            tokens = l.split('\t')
            if tokens[0] != "Lineage":
                if tokens[0].startswith("*"):
                    lin = tokens[0].lstrip("*")
                    lineages[lin] = f"Lineage reassigned. {tokens[1]}"
                lineages[tokens[0]]= tokens[1]
    return lineages
            
def make_summary_info(metadata, notes, json_outfile):
    # add lineages and sub lineages into a dict with verity's summary information about each lineage
    
    description_dict = get_description_dict(notes)

    summary_dict = collections.defaultdict(dict)

    # initialize dict with descriptions
    for lineage in description_dict:
        summary_dict[lineage] = {"Lineage":lineage,
                                "Countries":collections.Counter(),
                                "Earliest date": "",
                                "Count":0,
                                "Date":collections.Counter(),
                                "Travel history":collections.Counter(),
                                "Description":description_dict[lineage]}

    # compile data for json
    with open(metadata,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                country = row["country"]
                
                d = date.fromisoformat(row["sample_date"])
                travel_history = row["travel_history"]
                lineage = row["lineage"]

                if lineage != "" and lineage in description_dict:
                    
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
            except:
                pass

    for lineage in summary_dict:

        travel = summary_dict[lineage]["Travel history"]
        travel_info = ""
        for k in travel:
            travel_info += f"{travel[k]} {k}; "
        travel_info = travel_info.rstrip(";")
        summary_dict[lineage]["Travel history"] = travel_info

        countries = summary_dict[lineage]["Countries"]
        country_info = ""
        total = sum(countries.values())
        for k in countries.most_common(5):
            
            pcent = round((100*k[1])/total, 0)
            country_info += f"{k[0]} {pcent}%, "
        country_info = country_info.rstrip(", ")
        summary_dict[lineage]["Countries"] = country_info

        summary_dict[lineage]["Earliest date"] = str(summary_dict[lineage]["Earliest date"])

        date_objects = []
        for d in summary_dict[lineage]["Date"]:

            date_objects.append({"date":d,"count":summary_dict[lineage]["Date"][d]})
        summary_dict[lineage]["Date"] = date_objects

    with open(json_outfile, 'w', encoding='utf-8') as jsonf: 
        jsonf.write(json.dumps(summary_dict, indent=4)) 

    return summary_dict

def get_parent(lineage):
    alias = {
            "C":"B.1.1.1",
            "D":"B.1.1.25",
            "E":"B.1.5.12",
            "F":"B.1.36.17",
            "G":"B.1.258.2",
            "H":"B.1.1.67",
            "I":"B.1.1.217",
            "J":"B.1.1.250",
            "K":"B.1.1.277",
            "L":"B.1.1.10",
            "M":"B.1.1.294",
            "N":"B.1.1.33",
            "P":"B.1.1.28"}
    default_mapping = {"B":"A"}
    lin_list = lineage.split(".")
    
    if lineage == "B":
        parent = "A"

    elif lin_list[0] in alias and len(lin_list) == 2:
        parent = alias[lin_list[0]]
    
    else:
        parent = ".".join(lin_list[:-1])
    return parent

def sort_lineages(lin_list):
    splitted = [i.split(".") for i in lin_list]
    numeric = []
    for i in splitted:
        lin = [i[0]]
        for j in i[1:]:
            lin.append(int(j))
        numeric.append(lin)
    sorted_list = sorted(numeric)
    stringed = []
    for i in sorted_list:
        lin = [i[0]]
        for j in i[1:]:
            lin.append(str(j))
        stringed.append(lin)
    finished_list = ['.'.join(i) for i in stringed]
    return finished_list

def get_child_dict(lineages):
    child_dict = collections.defaultdict(list)
    alias = {"C":"B.1.1.1",
            "D":"B.1.1.25",
            "E":"B.1.5.12",
            "F":"B.1.36.17",
            "G":"B.1.258.2",
            "H":"B.1.1.67",
            "I":"B.1.1.217",
            "J":"B.1.1.277",
            "L":"B.1.1.10",
            "M":"B.1.1.294",
            "N":"B.1.1.33",
            "P":"B.1.1.28"}
    for lineage in lineages:
        lineage = lineage.lstrip("*")
        for i in range(len(lineage.split("."))):
            parent = ".".join(lineage.split(".")[:i+1])
            if parent in alias:
                a = alias[parent]
                for i in range(len(a.split("."))):
                    parent2 = ".".join(a.split(".")[:i+1])
                    child_dict[parent2].append(lineage)
            elif "B"==parent:
                child_dict[parent].append(lineage)
                child_dict["A"].append(lineage)
            else:
                child_dict[parent].append(lineage)
    children = {}
    for lineage in child_dict:
        children_lineages = sorted(list(set(child_dict[lineage])))
        children[lineage] = children_lineages
    return children

def get_children(lineage, child_dict):
    return child_dict[lineage]     

def update_pages():
    args = parse_args()

    website_dir = args.website_dir
    
    lineage_path = os.path.join(website_dir, "lineages")

    lineages = make_summary_info(args.metadata, args.lineage_notes, args.json_outfile)
    
    child_dict = get_child_dict(lineages)
    with open(f"{website_dir}/lineages.md","w") as fall:
        lineage_all = [i for i in lineages.keys() if not i.startswith("*")]
        sorted_all = sort_lineages(lineage_all)
        lineage_old = [i for i in lineages.keys() if i.startswith("*")]
        sorted_old = sort_lineages(lineage_old)
        for i in sorted_old:
            sorted_all.append(i)
        fall.write(f"---\nlayout: go_to_page\ntitle: 'Go to lineage:'\nchildren: {sorted_all}\n---\n")
    for lineage in lineages:
        if not lineage.startswith("*"):
            if lineage =="A":
                with open(f"{lineage_path}/lineage_{lineage}.md","w") as fw:
                    fw.write(f"""---\nlayout: lineage_page\ntitle: Lineage {lineage}\nlineage: {lineage}\nchildren: {sort_lineages(get_children(lineage, child_dict))}\n---\n""")
            else:
                with open(f"{lineage_path}/lineage_{lineage}.md","w") as fw:
                    fw.write(f"""---\nlayout: lineage_page\ntitle: Lineage {lineage}\nlineage: {lineage}\nparent: {get_parent(lineage)}\nchildren: {sort_lineages(get_children(lineage, child_dict))}\n---\n""")




if __name__ == '__main__':

    update_pages()
    