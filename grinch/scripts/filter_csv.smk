import csv 

rule filter_alignment:
    input:
        csv = config["lineages_csv"],
        full_csv = config["full_csv"]
    output:
        csv = config["outfile"]
    run:
        csv_len = 0
        lineages = {}
        with open(input.csv,"r") as f:
            for l in f:
                l = l.rstrip("\n")
                name,lineage = l.split(",")
                lineages[name]=lineage
                csv_len +=1

        with open(output.csv,"w") as fw:
            with open(input.full_csv,"r") as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames

                writer = csv.DictWriter(fw, fieldnames=header, lineterminator="\n")
                writer.writeheader()
                for row in reader:
                    name = row["sequence_name"]
                    name = name.replace("SouthAfrica","South_Africa")
                    if name in lineages:
                        new_row = row
                        new_row["lineage"] = lineages[name]
                        writer.writerow(new_row)
