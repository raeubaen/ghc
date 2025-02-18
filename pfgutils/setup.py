#!/usr/bin/env python
import sys
import os
from distutils.core import setup, Extension
from distutils.command.install import install


delattr(os, 'link')

def generateSQLiteDB(src, dst):
  import sqlite3
  import os
  # Execute commands
  if os.path.exists(dst):
    os.remove(dst)
  print("Prepare sqlite3 db")
  db = sqlite3.connect(dst, isolation_level=None)
  dbcur = db.cursor()
  if not src.startswith('/'):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), src))
  else:
    path = src
  with open(path, 'r') as f:
    sql = f.read()
    for line in sql.split('\n'):
      dbcur.execute(line.strip())
    db.commit()
    db.close()


packages = ["pfgutils"] + ["pfgutils." + x for x in ['channelstatus', "dqm"]]

datafiles = ['tnsnames.ora', 'ecalchannels.db', 'ecalchannels.sql']

generateSQLiteDB('pfgutils/ecalchannels.sql', 'pfgutils/ecalchannels.db')

setup(name="pfgutils", version="0.4", author="Latyshev Grigory", author_email="glatyshe@cern.ch",
  description="Python module for ECAL PFG projects", license="GPL", keywords="ecal postgresql database ROOT",
  url="https://gitlab.cern.ch/ECALPFG/pfgutils.git", packages=packages, package_data={'pfgutils': datafiles},
  requires=['cx_Oracle', 'requests', 'ROOT'],
  scripts=['pfgutils/channelstatus/dumppayload.py']
)
