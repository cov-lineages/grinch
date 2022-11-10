#!/usr/bin/env python3
import csv
import json
import os
import argparse
import collections
from datetime import date
from datetime import datetime
import shutil

def parse_args():
    parser = argparse.ArgumentParser(description='Update lineage web pages for cov-lineages.org')

    parser.add_argument("--website-dir", action="store", type=str, dest="website_dir")
    parser.add_argument('-m',"--metadata", action="store",type=str, dest="metadata")
    parser.add_argument('-n',"--lineage-notes", action="store",type=str, dest="lineage_notes")
    parser.add_argument("-d","--designations",action="store",dest="designations")
    parser.add_argument("-a","--alias",action="store",dest="alias")
    parser.add_argument("-o","--outfile",action="store",type=str, dest="json_outfile")
    return parser.parse_args()

def get_alias(alias_file):
    alias_dict = {}
    parsed_aliases= {}
    with open(alias_file, "r") as read_file:
        alias_dict = json.load(read_file)
    for i in alias_dict:
        if type(alias_dict[i]) != list and alias_dict[i]!="":
            parsed_aliases[i] = alias_dict[i]
    return parsed_aliases

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
    return_list = [dict() for idx in xrange(chunks)]
    idx = 0
    for k,v in input_dict.iteritems():
        return_list[idx][k] = v
        if idx < chunks-1:  # indexes start at 0
            idx += 1
        else:
            idx = 0
    return return_list

def make_summary_info(metadata, notes, designations, json_outfile):
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
                if lineage in ["B.1.1.7","B.1.351","P.1","B.1.617.2","B.1.1.529"] or lineage.startswith("BA."):
                    cut_off = datetime.strptime("2020-09-01", "%Y-%m-%d").date()
                
                    if lineage == "B.1.1.7": 
                        cut_off = datetime.strptime("2020-09-01", "%Y-%m-%d").date()
                    elif lineage == "B.1.351":
                        cut_off = datetime.strptime("2020-09-01", "%Y-%m-%d").date()
                    elif lineage == "P.1":
                        cut_off = datetime.strptime("2020-09-01", "%Y-%m-%d").date()
                    elif lineage == "B.1.617.2":
                        cut_off = datetime.strptime("2021-03-01", "%Y-%m-%d").date()
                    elif lineage == "B.1.1.529" or lineage.startswith("BA."):
                        cut_off = datetime.strptime("2021-09-01", "%Y-%m-%d").date()
                    
                    if d < cut_off: 
                        pass
                    else:
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
                else:
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
    for lineage in summary_dict:
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=3*365)
        if summary_dict[lineage]["Latest date"] < one_year_ago:
            continue
        else:
            del summary_dict[lineage]

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

        date_objects = []
        for d in summary_dict[lineage]["Date"]:

            date_objects.append({"date":d,"count":summary_dict[lineage]["Date"][d]})
        summary_dict[lineage]["Date"] = date_objects

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

def get_parent(lineage,alias):

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

def get_child_dict(lineages,alias):
    child_dict = collections.defaultdict(list)
            
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

    lineages = make_summary_info(args.metadata, args.lineage_notes, args.designations, args.json_outfile)
    alias = get_alias(args.alias)
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
                if lineage =="A":
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
    
