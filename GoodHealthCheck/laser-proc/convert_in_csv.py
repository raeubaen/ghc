import csv

columns_to_extract = [0, 1, 2, 5, 9, 10, 11, 12, 13, 18, 19]
headers = ["fed", "tcc", "tower", "ccu", "ieta", "iphi", "ix", "iy", "iz", "ietatt", "iphitt"]

input_file = "ecalchannels_db.txt"
output_file = "/eos/user/d/delvecch/www/PFG/ecalchannels.csv"

def extract_columns(input_file, output_file):
    with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        
        for line in infile:
            line = line.strip().strip("{}")
            values = line.split(",")
            selected_values = [values[i].strip() for i in columns_to_extract]
            writer.writerow(selected_values)

extract_columns(input_file, output_file)
print(f"File '{output_file}' creato con successo!")
