#!/usr/bin/env python

import os
import sys
import re
import subprocess
import hashlib

#import runsummary
#import Settings

# Dump Evgueni's table from Twiki page
class KnownProblems():
  def __init__(self, url = "https://twiki.cern.ch/twiki/bin/view/Main/EcalTTcurrentStatus?cover=print;raw=on"):
    p = subprocess.Popen(['curl', '-k', '-s', url],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    a = [l.strip() for l in output.split('\n') if re.match("^[-|]", l.strip())]
    tables_headers = [k.split('---+++ ')[1] for k in a if k.startswith('---+++ ')]
    tables = {}
    j = -1
    for i in range(len(a)):
      if '---+++' in a[i] and a[i].split('---+++ ')[1] in tables_headers:
        j += 1
        tables.update({tables_headers[j] : []})
        continue
      tables[tables_headers[j]].append(a[i])
    restables = {}
    for k in list(tables.keys()):
      headers = [ l.replace('*','').strip() for l in tables[k][0].split("|")[1:-1]]
      data = []
      for i in range(1, len(tables[k])):
        data.append ([l.replace('*','').strip() for l in tables[k][i].split("|")[1:-1]])
      restables.update({k : [k, headers, data]})
    self.table = restables

  def check(self, ylabel):
    # ylabel = "EB+09: TT60"
    if ylabel.startswith("EB"):
      table ='Problematic Trigger Towers - Barrel'
      sm = 'EB{0:+2d}'.format(int(re.findall('EB(.+):.*', ylabel)[0]))
    elif ylabel.startswith("EE"):
      table = 'Problematic FE - Endcap'
      sm = 'EE{0:+2d}'.format(int(re.findall('EE(.+):.*', ylabel)[0]))
    else:
      raise("Unknown ylabel")
    tt = int(ylabel.split("TT")[1])
    if table not in self.table:
      return False
    for i in self.getTable(table)[2]:
      if sm == i[1] and tt == int(i[3]):
        # print "Found '{0}' in KnownProblem table '{1}'!".format(ylabel, table)
        return True
    return False

  def getTable(self, table):
    return self.table[table]
