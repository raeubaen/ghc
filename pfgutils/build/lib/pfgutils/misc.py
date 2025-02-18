#!/usr/bin/env python

import hashlib
import os
import re
import shutil
import subprocess
import sys
import logging

from .Settings import tmpdir, certpath, keypath


def download(url, localpath, silent=True):
  """
    Downloads file with wget.
    File is first downloaded under a name 'tmpfile' and then renamed: the
    renaming operation is atomic, so the file is either fully downloaded or not
    downloaded at all.
  """
  tmpfile = os.path.join(tmpdir, hashlib.sha1(url + sys.platform).hexdigest() + ".tmp")
  if os.path.isfile(localpath) or os.path.isfile(tmpfile):
    return True  # file already downloaded
  # run wget
  ret = subprocess.call(['wget', '-q', '--no-check-certificate', '-t', '0', '-T', '2', '--certificate=' + certpath,
    '--private-key=' + keypath, url, '-O', tmpfile], stdout=sys.stdout, stderr=sys.stderr)
  if ret != 0:
    if not silent:
      logging.error("Cannot download file from " + url)
    try:
      os.remove(tmpfile)
    except:
      if not silent:
        logging.error("Cannot remove tmp file '{0}'".format(tmpfile))
    return False
  # atomic rename
  try:
    shutil.move(tmpfile, localpath)
  except:
    if not silent:
      logging.error("Cannot rename {0} to {1}".format(tmpfile, localpath))
    return False
  return True


def printTables(tables):
  """ Write tables in Textile format """

  import pfgutils.textile
  if not os.access('tables', os.X_OK):
    os.mkdir('tables')
  for table in tables:
    if not table:
      continue
    txt = pfgutils.textile.table(table[1], table[2])
    with open('tables/{0}'.format(table[0]), 'w') as f:
      f.write(txt)


# Dump Evgueni's table from Twiki page
class KnownProblems:
  def __init__(self, url="https://twiki.cern.ch/twiki/bin/view/Main/EcalTTcurrentStatus?cover=print;raw=on"):
    p = subprocess.Popen(['curl', '-k', '-s', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    if p.returncode != 0:
      logging.error(err)
      logging.error("Cannot retrieve info from CERN TWiki")
      self.table = {}
      return
    a = [l.strip() for l in output.split('\n') if re.match("^[-|]", l.strip())]
    tables_headers = [k.split('---+++ ')[1] for k in a if k.startswith('---+++ ')]
    tables = {}
    j = -1
    for i in range(len(a)):
      if '---+++' in a[i] and a[i].split('---+++ ')[1] in tables_headers:
        j += 1
        tables.update({tables_headers[j]: []})
        continue
      tables[tables_headers[j]].append(a[i])
    restables = {}
    for k in list(tables.keys()):
      headers = [l.replace('*', '').strip() for l in tables[k][0].split("|")[1:-1]]
      data = []
      for i in range(1, len(tables[k])):
        data.append([l.replace('*', '').strip() for l in tables[k][i].split("|")[1:-1]])
      restables.update({k: [k, headers, data]})
    self.table = restables

  def check(self, ylabel):
    # ylabel = "EB+09: TT60"
    if ylabel.startswith("EB"):
      table = 'Problematic Electronics Towers - Barrel'
      sm = 'EB{0:+2d}'.format(int(re.findall('EB(.+):.*', ylabel)[0]))
    elif ylabel.startswith("EE"):
      table = 'Problematic Electronics  Towers FE - Endcap'
      sm = 'EE{0:+2d}'.format(int(re.findall('EE(.+):.*', ylabel)[0]))
    else:
      raise Exception("Unknown ylabel")
    tt = int(ylabel.split("TT")[1])
    if table not in self.table:
      print("Table {0} not found".format(table))
      return False
    for i in self.getTable(table)[2]:
      if sm == i[1] and tt == int(i[3]):
        logging.info("Found '{0}' in KnownProblem table '{1}'!".format(ylabel, table))
        return True
    return False

  def getTable(self, table):
    if table in self.table:
      return self.table[table]
    else:
      return None, [], []


def printInfo(info):
  """ Returns Info page header """
  txt = "<table><tr><th>Property name</th><th>Value</th></tr>\n"
  for k in list(info.keys()):
    txt += "<tr><td>{0}</td><td>{1}</td></tr>\n".format(k, info[k])
  txt += "</table>"
  return txt


def splitList(l, n=50, barrier=3):
  """ Split 'l' per 'n' elements and returns list of lists """
  nw = []
  if n <= 0:
    return [l]
  for i in range(1, len(l) / n + 2):
    nw.append(l[(i - 1) * n: i * n])
  if len(nw) > 1 and len(nw[-1]) <= barrier:
    nw[-2] += nw[-1]
    del nw[-1]
  return nw

def isCollision(run):
  from pfgutils.oracle import getLumisections
  from .runsummary import RunSummary
  try:
    triggerbase = RunSummary().getRunInfo(run, 'TRIGGERBASE')
  except:
    # no such run
    triggerbase = ""
  if triggerbase is None:
    logging.warning("TRIGGERBASE for run {0} is None.".format(run))
    triggerbase = "" 
  if 'collision' not in triggerbase:
    return False
  lumis = getLumisections(run)
  stablels = sum([1 for x in lumis if x['BEAM1_STABLE'] == 1 and x['BEAM2_STABLE'] == 1])
  # run has mpre than 0 normal lumi
  return stablels > 0


def CollisionFilter(runlist):
  if type(runlist) != list and type(runlist) != tuple:
    runlist = [runlist]
  reslist = [x for x in runlist if isCollision(x)]
  return reslist


def BFieldFilter(runlist, limit=1):
  from .runsummary import RunSummary
  def check(rsarg, x):
    if limit > 0:
      return rsarg.getRunInfo(x, "BFIELD") >= limit
    else:
      return rsarg.getRunInfo(x, "BFIELD") < limit

  rs = RunSummary()
  return [x for x in runlist if check(rs, x)]


def isBMarked(run):
  from .runsummary import RunSummary
  rs = RunSummary()
  return rs.getRunInfo(run, 'BFIELD') < 1


def gettmp(directory=False):
  # type: () -> str
  p = subprocess.Popen(['mktemp'] + [[], ['-d']][directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = p.communicate()
  if p.returncode == 0:
    return stdout.strip()
  else:
    raise RuntimeError("ERROR:" + stderr)
