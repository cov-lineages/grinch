import geopandas
import csv
from collections import defaultdict
from collections import Counter
from collections import OrderedDict
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from epiweeks import Week

import pkg_resources
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import cm
import pandas as pd
import datetime as dt
import seaborn as sns
import numpy as np
import math
import os
import json
# #for testing
# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("--map")
# parser.add_argument("--figdir")
# parser.add_argument("--metadata")
# args = parser.parse_args()
# lineages_of_interest = ["B.1.1.7", "B.1.351"]
# ###

plt.rcParams.update({'font.size': 10})

def prep_map(world_map_file):

    world_map = geopandas.read_file(world_map_file)

    new_names = []
    for i in world_map["admin"]:
        new_name = i.replace(" ","_").upper()
        new_names.append(new_name)
    world_map["admin"] = new_names

    countries = []
    for i in world_map["admin"]:
        countries.append(i.replace(" ", "_"))

    return world_map, countries

def prep_inputs():

    omitted = ["ST_EUSTATIUS", "CRIMEA","Liechtenstein"] #too small, no shape files

    conversion_dict = {}

    conversion_dict["United_States"] = "United_States_of_America"
    conversion_dict["USA"] = "United_States_of_America"
    conversion_dict["Viet_Nam"] = "Vietnam"
    conversion_dict["Macedonia"] = "North_Macedonia"
    conversion_dict["NORTH MACEDONIA"] = "North_Macedonia"
    conversion_dict["Serbia"] = "Republic_of_Serbia"
    conversion_dict["Côte_d’Ivoire"] = "Ivory_Coast"
    conversion_dict["Cote_dIvoire"] = "Ivory_Coast"
    conversion_dict["CÔTE_D'IVOIRE"] = "Ivory_Coast"
    conversion_dict["Czech_Repubic"] = "Czech_Republic"
    conversion_dict["UK"] = "United_Kingdom"
    conversion_dict["Timor-Leste"] = "East_Timor"
    conversion_dict["DRC"] = "Democratic_Republic_of_the_Congo"
    conversion_dict["Saint_Barthélemy"] = "Saint-Barthélemy"
    conversion_dict["Saint_Martin"] = "Saint-Martin"
    conversion_dict["Curacao"] = "Curaçao"
    conversion_dict["St. Lucia"] = "Saint_Lucia"
    conversion_dict["GABORONE"] = "Botswana"

    conversion_dict2 = {}

    for k,v in conversion_dict.items():
        conversion_dict2[k.upper().replace(" ","_")] = v.upper().replace(" ","_")

    return conversion_dict2, omitted

def make_dataframe(metadata, conversion_dict2, omitted, lineage_of_interest, figdir, countries, world_map):

    locations_to_dates = defaultdict(list)
    country_to_new_country = {}
    country_new_seqs = {}
    country_dates = defaultdict(list)
    absent_countries = set()

    with open(metadata) as f:
        data = csv.DictReader(f)
        
        cut_off = dt.datetime.strptime("2020-09-01", "%Y-%m-%d").date()
        for seq in data:
            try:
                sample_date = dt.datetime.strptime(seq["sample_date"], "%Y-%m-%d").date()
                if sample_date < cut_off:
                    pass
                else:
                    if seq["lineage"] == lineage_of_interest:
                        seq_country = seq["country"].upper().replace(" ","_")
                        if seq_country == "CARIBBEAN":
                            seq_country = seq["sequence_name"].split("/")[0].upper().replace(" ","_")
                            
                        if seq_country in conversion_dict2:
                            new_country = conversion_dict2[seq_country]
                        else:
                            if seq_country not in omitted:
                                new_country = seq_country
                            else:
                                new_country = ""
                        
                        if new_country not in countries and new_country != "":
                            absent_countries.add(new_country)
                            pass
                        elif new_country != "":
                            try:
                                locations_to_dates[new_country].append(dt.datetime.strptime(seq["sample_date"], "%Y-%m-%d").date())
                            except:
                                pass
                        country_to_new_country[seq_country] = new_country
            except:
                pass
    

    loc_to_earliest_date = {}
    loc_seq_counts = {}

    df_dict = defaultdict(list)

    all_earliest_dates = []
    date_to_number = {}
    number_to_date = {}

    for country, dates in locations_to_dates.items():
        loc_seq_counts[country] = len(dates)
        loc_to_earliest_date[country] = min(dates)
    
    for i,v in loc_to_earliest_date.items():
        all_earliest_dates.append(v)

    earliest_date_count = Counter(all_earliest_dates)
    count = 0
    for i in sorted(earliest_date_count.keys()):
        date_to_number[i] = count
        number_to_date[count] = i
        count += 1
    
    for country, dates in locations_to_dates.items():  
        if country not in absent_countries:      
            df_dict["admin"].append(country.upper().replace(" ","_"))
            df_dict["earliest_date"].append(min(dates))
            df_dict["log_number_of_sequences"].append(np.log10(len(dates)))
            df_dict["number_of_sequences"].append(len(dates))
            df_dict["date_number"].append(date_to_number[min(dates)])


    info_df = pd.DataFrame(df_dict)

    with_info = world_map.merge(info_df, how="outer")

    with open(metadata) as f:
        data = csv.DictReader(f)    
        for seq in data:
            seq_country = seq["country"].upper().replace(" ","_")
            if seq_country == "CARIBBEAN":
                seq_country = seq["sequence_name"].split("/")[0].upper().replace(" ","_")
            if seq_country in country_to_new_country and seq_country not in absent_countries:
                new_country = country_to_new_country[seq_country]
                date = dt.datetime.strptime(seq["sample_date"], "%Y-%m-%d").date()
                if date >= loc_to_earliest_date[new_country]:
                    if new_country not in country_new_seqs:
                        country_new_seqs[new_country] = 1
                    else:
                        country_new_seqs[new_country] += 1
                    country_dates[new_country].append(date)
            elif seq_country in absent_countries:
                # print(seq_country)
                pass

    intermediate_dict = defaultdict(list)
    for place, total in country_new_seqs.items():
        intermediate_dict["admin"].append(place)
        intermediate_dict["Total sequences since first report"].append(total)
        
    intermediate_df = pd.DataFrame(intermediate_dict)

    new_info = info_df.merge(intermediate_df)
    new_row = []
    for i in new_info["admin"]:
        new_row.append(i.replace("_"," ").title())
    new_info["Country"] = new_row

    new_info.to_csv(f'{figdir}/{lineage_of_interest}_raw_data.csv')

    return with_info, locations_to_dates, country_new_seqs, loc_to_earliest_date, country_dates, number_to_date
    

def make_transmission_map(figdir, world_map, lineage, relevant_table):

    df_dict = defaultdict(list)
    info_dict = {}

    with open(relevant_table) as f:
        data = csv.DictReader(f)
        for line in data:
            df_dict["admin"].append(line["Country"].upper().replace(" ","_"))            
            if line["imported_local"] == "1":
                df_dict["transmission_number"].append(2)
                info_dict[line["Country"]] = 2
            elif line["imported_local"] == "0":
                df_dict["transmission_number"].append(1)
                info_dict[line["Country"]] = 1
            elif line["imported_local"] == "":
                df_dict["transmission_number"].append(0)
                info_dict[line["Country"]] = 0
            
    transmission_df = pd.DataFrame(df_dict)
    
    try:
        with_trans_info = world_map.merge(transmission_df, how="outer")
        trans_nona = with_trans_info.fillna(-1)
        trans_nona = trans_nona.dropna()

        colour_dict = {0.0:"#edd1cb", 1.0: '#aa688f', 2.0:'#2d1e3e', -1:"#d3d3d3"}
        label_dict = {0.0:"status_unknown",1.0:"imported_only",2.0:"local_transmission", -1:"No variant recorded"}

        fig, ax = plt.subplots(figsize=(11,11))
        trans_nona.plot(ax=ax, color=trans_nona["transmission_number"].map(colour_dict))

        patches = [plt.plot([],[], marker="o", ms=10, ls="", mec=None, color=colour_dict[i], 
                    label="{:s}".format(label_dict[i]) )[0]  for i in (label_dict.keys())]

        ax.legend(bbox_to_anchor=(-.03, 1.05),fontsize=8,frameon=False)

        ax.axis("off")            
        plt.savefig(os.path.join(figdir,f"Map_of_{lineage}_local_transmission.svg"), format='svg', bbox_inches='tight')
    except:
        print("Merge failed")
    return info_dict

def plot_date_map(figdir, with_info, lineage, number_to_date):

    muted_pal = sns.cubehelix_palette(as_cmap=True, reverse=True,rot=-.4, hue=0.7)
    
    fig, ax = plt.subplots(figsize=(10,10))

    with_info = with_info.to_crs("EPSG:4326")

    with_info.plot(ax=ax, cmap=muted_pal, legend=True, column="date_number", 
                    legend_kwds={'shrink':0.3},
                    #legend_kwds={'bbox_to_anchor':(-.03, 1.05),'fontsize':8,'frameon':False},
                    missing_kwds={"color": "lightgrey","label": "No variant recorded"})

    colourbar = ax.get_figure().get_axes()[1]
    yticks = colourbar.get_yticks()

    # print(yticks)
    newlabels = []
    for tick in yticks:
        try:
            newlabels.append(number_to_date[tick])
        except KeyError:
            # print(tick)
            newlabels.append("")

    # colourbar.set_yticklabels([number_to_date[ytick] for ytick in yticks])
    colourbar.set_yticklabels(newlabels)
    
    ax.axis("off")
    
    plt.savefig(os.path.join(figdir,f"Date_of_earliest_{lineage}_detected.svg"), format='svg', bbox_inches='tight')


def plot_count_map(figdir, with_info, lineage):

    muted_pal = sns.cubehelix_palette(as_cmap=True)
    dark = mpatches.Patch(color=muted_pal.colors[-1], label='Max sequences')
    light = mpatches.Patch(color=muted_pal.colors[0], label='1 sequence')
    none = mpatches.Patch(color="lightgrey", label='No variant record')
    fig, ax = plt.subplots(figsize=(10,10))

    with_info = with_info.to_crs("EPSG:4326")
    with_info.plot(ax=ax, cmap=muted_pal, legend=False, column="log_number_of_sequences", 
                    missing_kwds={"color": "lightgrey","label": "No variant recorded"})

    

    ax.legend(handles=[dark,light,none],bbox_to_anchor=(-.03, 1.05),fontsize=8,frameon=False)
    ax.axis("off")

    plt.savefig(os.path.join(figdir,f"Map_of_{lineage}_sequence_counts.svg"), format='svg', bbox_inches='tight')

def plot_bars(figdir, locations_to_dates, lineage):

    x = []
    y = []
    text_labels = []
    counts = []
    sortable_data = []

    for k in locations_to_dates:

        count = len(locations_to_dates[k])
        counts.append(count)
        sortable_data.append((count, k))
    
    for k in sorted(sortable_data, key = lambda x : x[0], reverse=True):
        count,location=k
        text_labels.append(count)
        y.append(np.log10(count))
        x.append(location.replace("_", " ").title())

    fig, ax = plt.subplots(1,1, figsize=(14,4), frameon=False)

    plt.bar(x,y,color="#86b0a6")

    [ax.spines[loc].set_visible(False) for loc in ['top','right']]

    yticks = ax.get_yticks()
    ax.set_yticklabels([(int(10**ytick)) for ytick in yticks])
    
    rects = ax.patches
    for rect, label in zip(rects, text_labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height + 0.1, label,
                ha='center', va='bottom', size=12, rotation=90)

    plt.ylabel("Sequence count\n(log10)")
    plt.xlabel("Country")
    plt.xticks(rotation=90)

    plt.savefig(os.path.join(figdir,f"Sequence_count_per_country_{lineage}.svg"), format='svg', bbox_inches='tight')

def flight_data_plot(figdir, flight_data,locations_to_dates,lineage, threshold, info_dict, central_loc):
    data = []
    with open(flight_data,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["flights"]) > threshold:
                data.append((row["country"], int(row["flights"])))

    sorted_data = sorted(data, key=lambda x : x[1], reverse=True)

    gisaid_counts = {}
    for i in locations_to_dates:
        if len(locations_to_dates[i]) != 0:
            loc = i.replace("_", " ").title()
            if loc == "United States Of America":
                loc = "United States of America"
            if loc != central_loc:
                gisaid_counts[loc] = len(locations_to_dates[i])

    counts = sorted(list(set(gisaid_counts.values())))

    muted_pal = sns.cubehelix_palette(gamma=1.2,n_colors=len(counts)+2)
    legend_patches = [mpatches.Patch(color="white", label='0')]

    muted_dict = {}
    legend_list = []
    for i in range(0,len(counts)):

        legend_list.append(mpatches.Patch(color=muted_pal[i], label=counts[i]))
        muted_dict[counts[i]] = muted_pal[i]

    legend_patches.append(legend_list[0])
    legend_patches.append(legend_list[-1])
    legend_patches.append(mpatches.Patch(color="lightgrey", label='Reported'))

    x,y = [],[]
    reported_dict = {}
    for i in sorted_data:
        x.append(i[0])
        y.append(i[1])

        if i[0] in info_dict:
            if info_dict[i[0]] == 2 or info_dict[i[0]] == 1 or info_dict[i[0]] == 0:
                reported_dict[i[0]] = "lightgrey"
            else:
                reported_dict[i[0]] = "white"
        else:
            reported_dict[i[0]] = "white"   

    d = {'country': x, 'flights': y}
    df = pd.DataFrame(data=d)

    muted_mapping = {}
    for i in x:
        if i in gisaid_counts:
            muted_mapping[i] = muted_dict[gisaid_counts[i]]
        else:
            if i in reported_dict:
                muted_mapping[i] = reported_dict[i]

    # print(muted_mapping)
    fig,ax = plt.subplots(figsize=(10,10))
    
    colours = [muted_mapping[i] for i in x ]
    # print(colours)
    customPalette = sns.set_palette(sns.color_palette(colours))
    sns.barplot(x="flights", y="country", palette=customPalette, edgecolor=".8", dodge=False,data=df)
    plt.xlabel("Total Number of Passengers")
    plt.ylabel("Country")
    ax.legend(handles=legend_patches,fontsize=8,frameon=False)
    [ax.spines[loc].set_visible(False) for loc in ['top','right']]

    plt.savefig(os.path.join(figdir,f"Air_traffic_by_destination_{lineage}.svg"), format='svg', bbox_inches='tight')


def plot_bars_by_freq(figdir, locations_to_dates, country_new_seqs, loc_to_earliest_date,lineage):

    freq_dict = {}
    for country, all_dates in locations_to_dates.items():
        total = country_new_seqs[country]
        freq = round(len(all_dates)/total,2)
        freq_dict[country] = freq

    x = []
    y = []
    z = []
    text_labels = []
    counts = []
    sortable_data = []

    for k in locations_to_dates:

        count = len(locations_to_dates[k])
        counts.append(count)
        freq = freq_dict[k]
        sortable_data.append((count, k, freq))
    
    for k in sorted(sortable_data, key = lambda x : x[0], reverse=True):
        count,location,freq=k
        text_labels.append(count)
        y.append(np.log10(count))
        x.append(location.replace("_", " ").title())
        z.append(freq)

    data = {'Country':x, 
            'Count':y,
            "Frequency":z} 
  
    # Create DataFrame 
    df = pd.DataFrame(data) 

    muted_pal = sns.cubehelix_palette(as_cmap=True)

    fig, ax = plt.subplots(1,1, figsize=(14,4), frameon=False)
    
    sns.barplot(x="Country", y="Count", data=df, dodge=False, palette=muted_pal(df["Frequency"]))
    plt.colorbar(cm.ScalarMappable(cmap=muted_pal),  shrink=0.5)
    [ax.spines[loc].set_visible(False) for loc in ['top','right',"left"]]

    yticks = ax.get_yticks()
    ax.set_yticklabels([(int(10**ytick)) for ytick in yticks])
    
    rects = ax.patches
    for rect, label in zip(rects, text_labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height + 0.1, label,
                ha='center', va='bottom',fontsize=8)
    
    plt.ylabel("Sequence count\n(log10)")
    plt.xlabel("Country")
    plt.xticks(rotation=90)

    plt.savefig(os.path.join(figdir,f"Sequence_count_per_country_{lineage}_by_frequency.svg"), format='svg', bbox_inches='tight')


def plot_frequency_new_sequences(figdir, locations_to_dates, country_new_seqs, loc_to_earliest_date, lineage):

    voc_frequency = {}
    text_label_dict = {}

    for country, all_dates in locations_to_dates.items():
        total = country_new_seqs[country]
        freq = len(all_dates)/total
        voc_frequency[country.replace("_"," ").title()] = freq
        text_label_dict[country.replace("_"," ").title()] = f"{len(all_dates)}/{total}"


    fig, ax = plt.subplots(figsize=(14,4))

    sort = {k: v for k, v in sorted(voc_frequency.items(), key=lambda item: item[1], reverse=True)}

    x = []
    y = []
    text_labels = []
    for key, value in sort.items():
        x.append(key)
        y.append(value)
        text_labels.append(text_label_dict[key])

        
    [ax.spines[loc].set_visible(False) for loc in ['top','right']]

    plt.ylabel("Frequency")
    plt.xlabel("Country")
    plt.xticks(rotation=90)

    plt.bar(x,y, color="#86b0a6")

    rects = ax.patches
    for rect, label in zip(rects, text_labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height + 0.01, label,
                ha='center', va='bottom', size=12, rotation=90)

    plt.savefig(os.path.join(figdir,f"Frequency_{lineage}_in_sequences_produced_since_first_new_variant_reported_per_country.svg"), format='svg', bbox_inches='tight')


def get_continent_mapping(continent_file):
    country_to_continent = {}
    with open(continent_file) as f:
        next(f)
        for l in f:
            toks = l.strip("\n").split(",")
            country_to_continent[toks[0]] = toks[1]

    return country_to_continent

def combine_into_continents(country_to_continent, locations_to_dates, country_dates):

    continent_to_variant = defaultdict(list)
    continent_to_all = defaultdict(list)
    
    for country, variant_dates in locations_to_dates.items():
        if country != "UNITED_KINGDOM":
            continent_to_variant[country_to_continent[country]].extend(variant_dates)
        else:
            continent_to_variant["UNITED_KINGDOM"] = variant_dates
    
    for country, all_dates in country_dates.items():
        if country != "UNITED_KINGDOM":
            continent_to_all[country_to_continent[country]].extend(all_dates)
        else:
            continent_to_all["UNITED_KINGDOM"] = all_dates

    return continent_to_variant, continent_to_all

def generate_rolling_frequency_count_data(figdir, locations_to_dates, country_dates, country_to_continent, lineage):

    continent_to_variant, continent_to_all = combine_into_continents(country_to_continent, locations_to_dates, country_dates)

    frequency_over_time = defaultdict(dict)
    counts_over_time = defaultdict(dict)

    # country_threshold = []
    for continent, variant_dates in continent_to_variant.items():#a dictionary with locations:[dates of variant sequences]
        
        day_one = min(variant_dates)
        date_dict = {}
        count_date_dict = {}
        
        overall_counts = Counter(continent_to_all[continent]) #counter of all sequences since the variant was first sampled in continent
        voc_counts = Counter(variant_dates) #so get a counter of variant sequences

        for i in variant_dates: #looping through all of the dates with a variant on
            day_frequency = voc_counts[i]/overall_counts[i]
            date_dict[i] = day_frequency #key=date, value=frequency on that day

            count_date_dict[i] = voc_counts[i] #key=date, value=count on that day

        #fill in days from first date of variant to most recent date of variant
        date_range = (max(date_dict.keys())-day_one).days
        for day in (day_one + dt.timedelta(n) for n in range(1,date_range)):
            if day not in date_dict.keys():
                date_dict[day] = 0

        count_date_range = (max(count_date_dict.keys())-day_one).days
        for day in (day_one + dt.timedelta(n) for n in range(1,count_date_range)):
            if day not in count_date_dict.keys():
                count_date_dict[day] = 0

        frequency_over_time[continent.replace("_"," ").title()] = OrderedDict(sorted(date_dict.items())) 
        counts_over_time[continent.replace("_"," ").title()] = OrderedDict(sorted(count_date_dict.items()))
    
    # print("Country threshold",country_threshold)
    frequency_df_dict = defaultdict(list)
    for k,v in frequency_over_time.items(): #key=country, value=dict of dates to frequencies
        for k2, v2 in v.items():
            frequency_df_dict['continent'].append(k)
            frequency_df_dict["date"].append(k2)
            frequency_df_dict["frequency"].append(v2)
    frequency_df = pd.DataFrame(frequency_df_dict)

    count_df_dict = defaultdict(list)
    for k,v in counts_over_time.items():#key=country, value=dict of dates to counts
        for k2, v2 in v.items():
            count_df_dict['continent'].append(k)
            count_df_dict["date"].append(k2)
            count_df_dict["count"].append(v2)
    count_df = pd.DataFrame(count_df_dict)

    return frequency_over_time, counts_over_time, frequency_df, count_df

def plot_count_and_frequency_rolling(figdir,locations_to_dates, country_dates, country_to_continent, lineage):

    frequency_over_time, counts_over_time, frequency_df, count_df = generate_rolling_frequency_count_data(figdir, locations_to_dates, country_dates, country_to_continent, lineage)

    # num_colours = 1
    # for i,v in frequency_over_time.items():
    #     if len(v) > 15 and i in country_threshold:
    #         num_colours+=1

    # muted_pal = sns.cubehelix_palette(n_colors=num_colours)
    muted_pal = sns.color_palette(palette=["#417F7A","#947383","#96C6AD","#525886","#937252",
                                        "#D18CAD","#A4A86F","lightgrey",
                                        "#982029"])

    fig, ax = plt.subplots(figsize=(14,4))
    c = 0
    for i,v in frequency_over_time.items():
        #if len(v) > 10 and i in country_threshold:#so we do this for countries with more than ten days between the first variant sequence and last variant sequence
        c +=1
        relevant = frequency_df.loc[frequency_df["continent"] == i]
        y = relevant['frequency'].rolling(5).mean()    
        x = list(frequency_df.loc[frequency_df["continent"] == i]["date"])

        plt.plot(x,y, label = i, color=muted_pal[c],linewidth=2)
        [ax.spines[loc].set_visible(False) for loc in ['top','right']]
        plt.xticks(rotation=90)

    plt.ylim(bottom=0)
    plt.legend(frameon=False,fontsize=8)
    plt.ylabel("Frequency (7 day rolling average)")
    plt.xlabel("Date")

    plt.savefig(os.path.join(figdir,f"Rolling_average_{lineage}_frequency_per_continent.svg"), format='svg', bbox_inches='tight')

    
    fig, ax = plt.subplots(figsize=(14,4))
    c = 0
    for i,v in counts_over_time.items():
        # if len(v) > 10 and i in country_threshold:
        c+=1
        relevant = count_df.loc[count_df["continent"] == i]
        y = []
        for value in relevant['count'].rolling(7).mean():
            y.append(np.log10(value+1))
        x = list(count_df.loc[count_df["continent"] == i]["date"])

        plt.plot(x,y, label = i, color=muted_pal[c],linewidth=2)
        [ax.spines[loc].set_visible(False) for loc in ['top','right']]
        plt.xticks(rotation=90)

    
    plt.legend(frameon=False,fontsize=8)
    plt.ylabel("Count (7 day rolling average)")
    plt.xlabel("Date")
    ax.set_ylim(bottom=0)
    yticks = ax.get_yticks()
    ax.set_yticklabels([(int(10**ytick)) for ytick in yticks])
    plt.savefig(os.path.join(figdir,f"{lineage}_count_per_continent.svg"), format='svg', bbox_inches='tight')


def cumulative_seqs_over_time(figdir, locations_to_dates,lineage):

    dates = []
    epiweek_lst = []

    for k,v in locations_to_dates.items():
        dates.extend(v)
        
    date_counts = Counter(dates)

    seq_number = 0
    cum_counts = {}
    for date, value in sorted(date_counts.items()):
        seq_number = seq_number + value
        cum_counts[date] = seq_number

    for i in dates:
        epiweek_lst.append(Week.fromdate(i).startdate())
    
    epiweek_counts = Counter(epiweek_lst)
    sorted_epiweeks = OrderedDict(sorted(epiweek_counts.items()))

    fig, ax1 = plt.subplots(1,1,figsize=(14,4))

    ax1.bar(list(sorted_epiweeks.keys()), list(sorted_epiweeks.values()), color="#86b0a6", width=5)
    ax2 = ax1.twinx()
    ax2.plot(list(cum_counts.keys()), list(cum_counts.values()),linewidth=3,color="dimgrey")
    # ylims = (0,4000) 
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)

    ax1.xaxis.set_tick_params(rotation=90)
    ax1.set_xlabel("Date")
    ax2.set_ylabel("Total")
    ax1.set_ylabel("Sequence count")
    # ax2.set_ylim(ylims)
    
    plt.savefig(os.path.join(figdir,f"Cumulative_sequence_count_over_time_{lineage}.svg"), format='svg', bbox_inches='tight')

def plot_figures(world_map_file, figdir, metadata, continent_file, flight_data_path):
    
    lineage_summary = {}
    lineage_info = pkg_resources.resource_filename('grinch', f'data/lineage_info.json')
    with open(lineage_info,"r") as f:
        read_info = json.load(f)

    lineages_of_interest = []
    for lineage in read_info:
        lineages_of_interest.append(lineage)
        lin_data = read_info[lineage]
        lineage_summary[lineage] = {
            "threshold": lin_data["threshold"],
            "central_loc": lin_data["detected"],
            "flight_data": None,
            "import_data" : None
        }
        if lin_data["threshold"] != "NA":
            lineage_summary[lineage]["flight_data"] = os.path.join(flight_data_path, f"{lineage}.csv")
        if lin_data["import_data"] == "Y":
            lineage_summary[lineage]["import_data"] = pkg_resources.resource_filename('grinch', f'data/local_imported_{lineage}.csv')

    world_map, countries = prep_map(world_map_file)
    country_to_continent = get_continent_mapping(continent_file)
    conversion_dict2, omitted = prep_inputs()

    for lineage in lineages_of_interest:
        print(lineage)
        with_info, locations_to_dates, country_new_seqs, loc_to_earliest_date, country_dates, number_to_date = make_dataframe(metadata, conversion_dict2, omitted, lineage, figdir, countries, world_map)

        lineage_data = lineage_summary[lineage]
        threshold = lineage_data["threshold"]
        flight_data = lineage_data["flight_data"]
        central_loc = lineage_data["central_loc"]
        relevant_table = lineage_data["import_data"]

        if relevant_table:
            info_dict = make_transmission_map(figdir, world_map, lineage, relevant_table)

        if flight_data:
            flight_data_plot(figdir, flight_data,locations_to_dates,lineage, threshold, info_dict, central_loc)

        
        plot_date_map(figdir, with_info, lineage, number_to_date)
        print(f"{lineage} date map")
        plot_count_map(figdir, with_info, lineage)
        print(f"{lineage} count map")
        plot_bars(figdir, locations_to_dates, lineage)
        print(f"{lineage} bars")
        plot_bars_by_freq(figdir, locations_to_dates, country_new_seqs, loc_to_earliest_date,lineage)
        cumulative_seqs_over_time(figdir,locations_to_dates,lineage)
        print(f"{lineage} cumseq")
        plot_frequency_new_sequences(figdir, locations_to_dates, country_new_seqs, loc_to_earliest_date, lineage)
        plot_count_and_frequency_rolling(figdir,locations_to_dates, country_dates, country_to_continent, lineage)

# plot_figures(args.map, args.figdir, args.metadata, lineages_of_interest, False)







