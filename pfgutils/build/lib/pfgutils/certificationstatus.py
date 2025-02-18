#!/usr/bin/env python

import sys
import re
import subprocess
import logging

url = 'https://cms-service-dqm.web.cern.ch/cms-service-dqm/CAF/certification/Collisions17/13TeV/CertSummary/status.Collisions17.html'


def getCertificationStatus():
  p = subprocess.Popen(['curl', '-s', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = p.communicate()
  text = stdout.strip()
  ntr = len(re.findall("<tr>", text))
  nth = len(re.findall("<th>", text))
  N = nth - ntr + 1
  arr = re.findall(">([^<>]*)</t[dh]>", text)
  data = []
  for i in range(len(arr) / N):
    tmp = []
    for cell in range(N):
      cellx = i * N + cell
      try:
        value = int(arr[cellx])
      except:
        value = arr[cellx]
      tmp.append(value)
    data.append(tmp)
  return data


def filterStatusByKey(key, filtervalue="To be checked"):
  data = getCertificationStatus()
  if key not in data[0]:
    logging.warning("Key '{0}' not found on the page '{1}'".format(key, url))
    return []
  hind = data[0].index(key)
  return [(x[0], x[hind]) for x in data if x[hind] == filtervalue]
