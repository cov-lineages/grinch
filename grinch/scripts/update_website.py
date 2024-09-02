#!/usr/bin/env python3
import csv
import json
import os
import sys
import argparse
import collections
from datetime import date
from datetime import datetime
from datetime import timedelta
import shutil

from grinch.figure_generation.figurefunks import get_alias_dict, expand_alias

vocs = ["B.1.1.7","B.1.351","P.1","B.1.617.2","B.1.1.529", "A.1"]
cut_off_dict = {"B.1.1.7": "2020-09-01",
                "B.1.351": "2020-09-01",
                "P.1": "2020-09-01",
                "B.1.617.2": "2021-03-01",
                "B.1.1.529": "2021-09-01"}

def parse_args():
    parser = argparse.ArgumentParser(description='Update lineage web pages for cov-lineages.org')

    parser.add_argument("--website-dir", action="store", type=str, dest="website_dir")
    parser.add_argument('-m',"--metadata", action="store",type=str, dest="metadata")
    parser.add_argument('-n',"--lineage-notes", action="store",type=str, dest="lineage_notes")
    parser.add_argument("-d","--designations",action="store",dest="designations")
    parser.add_argument("-a","--alias",action="store",dest="alias")
    parser.add_argument("-o","--outfile",action="store",type=str, dest="json_outfile")
    return parser.parse_args()

def check_voc(lineage, alias_dict):
    if lineage in vocs:
        return lineage
    expanded_lineage = expand_alias(lineage, alias_dict)
    if not expanded_lineage:
        return None
    for voc in vocs:
        if expanded_lineage.startswith(voc + "."):
            return voc
    return None
    

def get_description_dict(description_file):
    lineages = {}
    with open(description_file,"r") as f:
        for l in f:
            l = l.rstrip("\n")
            tokens = l.split('\t')
            try:
                if tokens[0] != "Lineage":
                    if tokens[0].startswith("*"):
                        lin = tokens[0].lstrip("*")
                        lineages[lin] = f"Lineage reassigned. {tokens[1]}"
                    lineages[tokens[0]]= tokens[1]
            except:
                print(tokens)
                print(tokens[0] in lineages)
    return lineages

def get_conversion_dict():
    conversion_dict = {}
    conversion_dict["United_States"] = "United States of America"
    conversion_dict["USA"] = "United States of America"
    conversion_dict["Viet_Nam"] = "Vietnam"
    conversion_dict["North_Macedonia"] = "Macedonia"
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

def split_dict_chunks(input_dict, chunks=2):
    "Returns a list of dictionaries."
    return_list = [dict() for idx in range(chunks)]
    idx = 0
    for k,v in input_dict.items():
        return_list[idx][k] = v
        if idx < chunks-1:  # indexes start at 0
            idx += 1
        else:
            idx = 0
    return return_list

def make_summary_info(metadata, notes, designations, json_outfile, alias_dict):
    # add lineages and sub lineages into a dict with verity's summary information about each lineage
    not_found = []
    description_dict = get_description_dict(notes)

    summary_dict = collections.defaultdict(dict)

    # initialize dict with descriptions
    for lineage in description_dict:
        summary_dict[lineage] = {"Lineage":lineage,
                                "Countries":collections.Counter(),
                                "Country counts":collections.defaultdict(dict),
                                "Earliest date": "",
                                "Latest date": "",
                                "Number designated":0,
                                "Number assigned":0,
                                "Date":collections.Counter(),
                                "Travel history":collections.Counter(),
                                "Description":description_dict[lineage]}
    
    with open(designations,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lineage = row["lineage"]
            if lineage in summary_dict:
                summary_dict[lineage]["Number designated"]+=1
            else:
                not_found.append(lineage)
    

    # compile data for json
    conversion_dict = get_conversion_dict()
    with open(metadata,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                country = row["country"]
                
                d = date.fromisoformat(row["sample_date"])
                travel_history = row["edin_travel"]
                lineage = row["lineage"]
                voc = check_voc(lineage, alias_dict)
                if voc:
                    cut_off = datetime.strptime(cut_off_dict[voc], "%Y-%m-%d").date()
                    if d < cut_off:
                        pass

                if lineage != "" and lineage in description_dict:
                        
                    if country == "Caribbean":
                        country = row["sequence_name"].split("/")[0]
                        
                    if country in conversion_dict:
                        country = conversion_dict[country]
                        
                    summary_dict[lineage]["Countries"][country]+=1
                        
                    if summary_dict[lineage]["Earliest date"]:
                        if d < summary_dict[lineage]["Earliest date"]:
                            summary_dict[lineage]["Earliest date"] = d
                    else:
                        summary_dict[lineage]["Earliest date"] = d

                    if summary_dict[lineage]["Latest date"]:
                        if d > summary_dict[lineage]["Latest date"]:
                            summary_dict[lineage]["Latest date"] = d
                    else:
                        summary_dict[lineage]["Latest date"] = d
                        
                    summary_dict[lineage]["Date"][str(d)] +=1
                    if country not in summary_dict[lineage]["Country counts"]:
                        summary_dict[lineage]["Country counts"][country] = collections.Counter()
                        summary_dict[lineage]["Country counts"][country][str(d)]+=1
                    else:
                        summary_dict[lineage]["Country counts"][country][str(d)]+=1

                    summary_dict[lineage]["Number assigned"] +=1 

                    if travel_history:
                        summary_dict[lineage]["Travel history"][travel_history]+=1
            except:
                pass

    one_year_ago = datetime.now() - timedelta(days=120)
    old_lineages = []

    vocs_and_parents = get_voc_parents(alias_dict)
    for lineage in summary_dict:
        if summary_dict[lineage]["Latest date"] == "" or summary_dict[lineage]["Latest date"] < one_year_ago.date():
            if not lineage in vocs_and_parents:
                print("Old lineage not in vocs", lineage, vocs_and_parents)
                old_lineages.append(lineage)

        travel = summary_dict[lineage]["Travel history"]
        travel_info = ""
        for k in travel:
            travel_info += f"{travel[k]} {k}; "
        travel_info = travel_info.rstrip(";")
        summary_dict[lineage]["Travel history"] = travel_info

        countries = summary_dict[lineage]["Countries"]
        
        country_info = ""
        total = sum(countries.values())
        country_count_list = []
        for country in summary_dict[lineage]["Country counts"]:
            date_counts = summary_dict[lineage]["Country counts"][country]
            country_count = {"country": country,
                             "counts":[]}
            for day in sorted(date_counts):
                country_count["counts"].append({"date":day,"count":date_counts[day]})
            country_count_list.append(country_count)

        summary_dict[lineage]["Country counts"] = country_count_list

        for k in countries.most_common(5):
            
            pcent = round((100*k[1])/total, 0)
            country_info += f"{k[0]} {pcent}%, "
        country_info = country_info.rstrip(", ")
        summary_dict[lineage]["Countries"] = country_info
        
        summary_dict[lineage]["Earliest date"] = str(summary_dict[lineage]["Earliest date"])
        summary_dict[lineage]["Latest date"] = str(summary_dict[lineage]["Latest date"])

        date_objects = []
        for d in summary_dict[lineage]["Date"]:

            date_objects.append({"date":d,"count":summary_dict[lineage]["Date"][d]})
        summary_dict[lineage]["Date"] = date_objects

    with open(json_outfile.replace(".json",".full.json"), 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(summary_dict, indent=4))

    print("Old lineages", old_lineages)
    for lineage in old_lineages:
        del summary_dict[lineage]
    for lineage in summary_dict:
        del summary_dict[lineage]["Latest date"]

    number_chunks = 1
    if number_chunks > 1:
        summary_chunks = split_dict_chunks(summary_dict, number_chunks)
        for i in range(number_chunks):
            with open(json_outfile.replace(".json", "_%i.json" %i), 'w', encoding='utf-8') as jsonf:
                jsonf.write(json.dumps(summary_chunks[i], indent=4))
    else:
        with open(json_outfile, 'w', encoding='utf-8') as jsonf:
            jsonf.write(json.dumps(summary_dict, indent=4))
    print("Lineages not found", list(set(not_found)))
    return summary_dict

def collapse_lineage_list(lin_list, alias_dict):
    preface = ".".join(lin_list[:4])
    while len(lin_list) > 5 and preface in alias_dict:
        preface = ".".join(lin_list[:4])
        lin_list = [alias_dict[preface]]
        lin_list.extend(lin_list[4:])
    return lin_list
   
def get_parent(lineage,alias):

    lin_list = lineage.split(".")

    if lineage == "B":
        return "A"

    if len(lin_list) == 1 and lineage.startswith("X"):
        return None

    if len(lin_list) == 2 and lin_list[0] in alias and not lin_list[0].startswith("X"):
        new_lin_list = alias[lin_list[0]].split(".")
        new_lin_list.append(lin_list[1])
        lin_list = new_lin_list
   
    if len(lin_list) > 5:
        lin_list = collapse_lineage_list(lin_list, alias)

    parent = ".".join(lin_list[:-1])
    return parent

def get_voc_parents(alias_dict):
    vocs = ["B.1.1.7","B.1.351","P.1","B.1.617.2","B.1.1.529"]
    vocs_and_parents = set()
    for v in vocs:
        parent = v
        while parent != "A" and not parent.startswith("X"):
            vocs_and_parents.add(parent)
            new_parent = get_parent(parent, alias_dict)
            if new_parent == parent:
                break
            else:
                parent = new_parent
    return list(vocs_and_parents)
       
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
    assert len(lin_list) == len(finished_list)
    return finished_list

def get_child_dict(lineages,alias_dict):
    child_dict = collections.defaultdict(list)
    for lineage in lineages:
        lineage = lineage.lstrip("*")
        parent = lineage
        child_dict[parent].append(lineage)
        count = 0
        while parent and parent != "A" and count < 200:
            new_parent = get_parent(parent, alias_dict)
            if not new_parent or new_parent == parent:
                break
            else:
                parent = new_parent
            child_dict[parent].append(lineage)
            count += 1
            if count == 200:
                print("had a loop", parent, alias_dict)
                sys.exit()
            
    for key in child_dict:
        if key.startswith("X"):
            print(key, child_dict[key])
    children = {}
    for lineage in child_dict:
        children_lineages = sorted(list(set(child_dict[lineage])))
        children[lineage] = children_lineages
    for key in children:
        if key.startswith("X"):
            print(key, child_dict[key])
    return children

def get_children(lineage, child_dict):
    return child_dict[lineage]     

def update_pages():
    args = parse_args()

    website_dir = args.website_dir
    
    lineage_path = os.path.join(website_dir, "lineages")

    alias = get_alias_dict(args.alias)
    lineages = make_summary_info(args.metadata, args.lineage_notes, args.designations, args.json_outfile, alias)
    child_dict = get_child_dict(lineages,alias)
    c=0

    with open(f"{website_dir}/data/lineages.yml","w") as lineage_file:
        for lineage in lineages:
            if not lineage.startswith("*"):
                c +=1
                if c<500:
                    lineage_dir = os.path.join(lineage_path, "lineages1")
                elif c<1000:
                    lineage_dir = os.path.join(lineage_path, "lineages2")
                elif c<1500:
                    lineage_dir = os.path.join(lineage_path, "lineages3")
                elif c<2000:
                    lineage_dir = os.path.join(lineage_path, "lineages4")
                elif c<2500:
                    lineage_dir = os.path.join(lineage_path, "lineages5")
                else:
                    lineage_dir = os.path.join(lineage_path, "lineages6")
                if not os.path.exists(lineage_dir):
                    os.mkdir(lineage_dir)
                if lineage.startswith("X"):
                    print(lineage, get_children(lineage, child_dict), get_parent(lineage,alias))
                if lineage =="A" or (lineage.startswith("X") and "." not in lineage):
                    with open(f"{lineage_dir}/lineage_{lineage}.md","w") as fw:
                        fw.write(f"""---\npermalink: /lineages/lineage_{lineage}.html\nlayout: lineage_page\ntitle: Lineage {lineage}\nredirect_to: ../lineage.html?lineage={lineage}\nlineage: {lineage}\nchildren: {sort_lineages(get_children(lineage, child_dict))}\n---\n""")
                
                    lineage_file.write("- name: " + lineage + "\n")
                    lineage_file.write("  children:\n")

                    for child in sort_lineages(get_children(lineage, child_dict)):
                        lineage_file.write("      - " + child + "\n")

                else:
                    with open(f"{lineage_dir}/lineage_{lineage}.md","w") as fw:
                        fw.write(f"""---\npermalink: /lineages/lineage_{lineage}.html\nlayout: lineage_page\ntitle: Lineage {lineage}\nredirect_to: ../lineage.html?lineage={lineage}\nlineage: {lineage}\nparent: {get_parent(lineage,alias)}\nchildren: {sort_lineages(get_children(lineage, child_dict))}\n---\n""")

                    lineage_file.write("- name: " + lineage + "\n")
                    lineage_file.write("  children:\n")

                    for child in sort_lineages(get_children(lineage, child_dict)):
                        lineage_file.write("      - " + child + "\n")

                        lineage_file.write("  parent: " + get_parent(lineage,alias) + "\n")

        copyFile = shutil.copy(f"{website_dir}/data/lineages.yml", f"{website_dir}/_data/lineages.yml")
if __name__ == '__main__':

    update_pages()
    
