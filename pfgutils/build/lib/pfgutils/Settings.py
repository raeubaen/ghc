#!/usr/bin/env python

import os
# Settings

max_good_status = 3

# Oracle
Oracle = { # Oracle user
  'user': 'CMS_ECAL_R', # Oracle password
  'password': '3c4l_r34d3r', # Oracle SID
  'SID': 'cms_tstore.cern.ch'}

Database = { # PostgreSQL options
  'driver': 'postgresql', 'options': {'host': "128.142.136.43", 'user': 'pfgreadonly', 'password': 'ecalpfg'}
}

tmpdir = "/tmp"
rootpath = os.path.join("/var/www/downloads")
certpath = os.path.join(os.path.expanduser('~'), '.globus/usercert.pem')
keypath = os.path.join(os.path.expanduser('~'), '.globus/userkey.pem')
cacert = "/etc/ssl/certs/ca-bundle.crt"
