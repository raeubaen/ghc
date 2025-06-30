import os, sys, urllib.request, urllib.error, urllib.parse, http.client, json
import array

ident = "DQMToJson/1.0 python/%d.%d.%d" % sys.version_info[:3]



def x509_params():
    key_file = cert_file = None
    
    x509_path = os.getenv("X509_USER_PROXY", None)
    if x509_path and os.path.exists(x509_path):
        key_file = cert_file = x509_path
        
    if not key_file:
        x509_path = os.getenv("X509_USER_KEY", None)
        if x509_path and os.path.exists(x509_path):
            key_file = x509_path

    if not cert_file:
        x509_path = os.getenv("X509_USER_CERT", None)
        if x509_path and os.path.exists(x509_path):
            cert_file = x509_path

    if not key_file:
        x509_path = os.getenv("HOME") + "/.globus/userkey.pem"
        if os.path.exists(x509_path):
            key_file = x509_path

    if not cert_file:
        x509_path = os.getenv("HOME") + "/.globus/usercert.pem"
        if os.path.exists(x509_path):
            cert_file = x509_path

    if not key_file or not os.path.exists(key_file):
        print("no certificate private key file found", file=sys.stderr)
        sys.exit(1)

    if not cert_file or not os.path.exists(cert_file):
        print("no certificate public key file found", file=sys.stderr)
        sys.exit(1)

    print(("Using SSL private key", key_file))
    print(("Using SSL public key", cert_file))
    return key_file, cert_file


def dqm_get_json(buildopener, run, dataset, folder, plotname):
    if dataset != "/Global/Online/ALL/":
        print(f"Error in dataset of run {run}, it should be: /Global/Online/ALL/\nControl the runlist file in input")
        print("Exiting from the execution of the program")
        sys.exit(1)

    serverurl = 'https://cmsweb.cern.ch/dqm/online'
    path = f"jsrootfairy/archive/{run}/{dataset}/{folder}/{urllib.parse.quote(plotname)}"
    path = path.replace("//", "/")
    url = f"{serverurl}/{path}"

    print(f"Reading: {url}")
    datareq = urllib.request.Request(url)
    datareq.add_header('User-agent', ident)

    return buildopener.open(datareq).read().decode("utf-8")
