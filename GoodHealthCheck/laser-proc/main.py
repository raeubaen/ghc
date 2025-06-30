import os, sys, urllib.request, urllib.error, urllib.parse, http.client
import ROOT
import argparse
import importlib
import json
import pandas as pd
import traceback
from pathlib import Path
from json_handler import x509_params, dqm_get_json
from cert_opener import X509CertAuth, X509CertOpen



#from a csv file to a dict
def read_csv(file_path):
    df = pd.read_csv(file_path)
    data_list = df.to_dict(orient="records")
    return data_list


#read the plugins
def load_plugins(json_path):
    with open(json_path, "r") as file:
        data = json.load(file)
    return data.get("Plugins", [])


def main():
    ROOT.gROOT.SetBatch(True)

    #set the certificate and the key needed
    X509CertAuth.ssl_key_file, X509CertAuth.ssl_cert_file = x509_params()
    buildopener = urllib.request.build_opener(X509CertOpen())

    #create parser to read arguments from command line
    parser = argparse.ArgumentParser(description="csv file to get run and dataset information")
    parser.add_argument('runlist_csvfile_path', type=str, help="Path to the runlist file")
    parser.add_argument('plot_folder', type=str, help="Path to save plots")
    args = parser.parse_args()
    
    #read the csv input file and convert into a list of dict: [{"run": 294295, "dataset": "blablabla"}, {...}, ...]
    runlist = read_csv(args.runlist_csvfile_path)
    if runlist is None:
        print("Error in reading the runlist file\nExiting from the execution of the program")

    #read the plugins
    plugins = load_plugins(f"{os.path.dirname(os.path.realpath(__file__))}/conf.json")
    #plugins = load_plugins("./conf_prova.json")
    print(f"List of plugins: {plugins}")

    #plugins directory path
    plugins_dir = Path(__file__).parent / "plugins"
    sys.path.append(str(plugins_dir))

    #loop over plugins
    for plugin in plugins:
        print(f"Caricamento del plugin: {plugin}")
        mod = importlib.import_module(f"{plugin}")
        instance = getattr(mod, f"{plugin}")(buildopener)
        #loop over runs
        for item in runlist:
            run = item["run"]
            dataset = item["dataset"]
            print(f"Run number: {run}")
            #instantiate the plugins class
            try:
              instance.process_one_run(item)
            except Exception:
              print(f"Failed to process: {run} {dataset} {plugin}")
              print(traceback.format_exc())
        #create the history plot
        #instance.create_history_plots(args.plot_folder)
        print("\n")
        
if __name__ == "__main__":
    main()
