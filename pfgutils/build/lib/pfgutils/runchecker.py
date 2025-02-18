#!/usr/bin/env python

import ROOT
import os
import re
import sys

from .Settings import rootpath
from .connection import dqms
from .misc import download, CollisionFilter

cache = {}


def check_onlinedqm(run, filt=""):
  dqm = dqms['online']
  dataset = "{0:05d}xxxx".format(int(str(run)[:-4]))
  if len([x for x in dqm._getRunFiles(dataset, run) if "Ecal" in x]) == 0:
    return False
  return True


def check_physdecl(run, filt=""):
  """ Checks if Physics declared flag is ON """
  import pfgutils.dqm.json
  data = pfgutils.dqm.json.get(run, "Info/EventInfo/reportSummaryMap")
  if data is None:
    # It also affects to "Live" DQM plots
    return False
  else:
    h = pfgutils.dqm.json.JSON2ROOT(data)
    ybin = 26  # PhysDecl
    for xbin in range(1, h.GetNbinsX() + 1):
      if h.GetBinContent(xbin, ybin) == 1:  # green cell
        return True
    return False


def check_digientries(run, filt):
  import pfgutils.dqm.json
  data = pfgutils.dqm.json.get(run, "EcalBarrel/EBSummaryClient/EBOT digi occupancy summary 1D")
  if data is None:
    return False
  _entries = data['hist']['stats']['entries']
  if eval(filt.replace("digientries", "_entries")):
    return True
  else:
    return False


def check_processedevents(run, filt):
  tmppath = os.path.join(rootpath, 'DQM_V0001_Ecal_R{0:09d}.root'.format(run))
  pathfmt = 'https://cmsweb.cern.ch/dqm/online/data/browse/Original/{0:05d}xxxx/{1:07d}xx/DQM_V0001_{3}_R{2:09d}.root'
  url = pathfmt.format(int(run / 10000), int(run / 100), run, 'Ecal')
  if not download(url, tmppath, True):
    return False
  try:
    f = ROOT.TFile(tmppath)
  except:
    return False
  for k in f.Get('/DQMData/Run {0}/Ecal/Run summary/EventInfo'.format(run)).GetListOfKeys():
    if k.IsFolder():
      continue
    if 'processedEvents' in str(k):
      _value = int(re.findall("=(.*)<", str(k))[0])
      if eval(filt.replace("processedevents", "_value")):
        f.Close()
        return True
  f.Close()
  return False

def check_l1trigger(run, filt):
  from pfgutils.runsummary import RunSummary
  rs = RunSummary()
  _value = rs.getRunInfo(run, 'TRIGGERS')
  return eval(filt.replace("l1trigger", "_value"))

def check_collision(run, filt=""):
  return run in CollisionFilter([run])


def checkRun(run, filterstr=""):
  """ Checks run by some parameters """
  global cache
  thismodule = sys.modules[__name__]
  run = int(run)
  filterstr = filterstr.lower()
  rc = []
  checklist = [x.split("_")[1] for x in dir(thismodule) if "check_" in x]
  for filt in filterstr.split(":"):
    fname = [x for x in checklist if x in filt]
    if len(fname) != 0:
      if fname[0] not in cache:
        cache[fname[0]] = {}
      if run in cache[fname[0]]:
        rc.append(cache[fname[0]][run])
      else:
        func = getattr(thismodule, "check_" + fname[0])
        try:
          r = func(run, filt)
          cache[fname[0]][run] = r
          rc.append(r)
        except:
          cache[fname[0]][run] = False
          rc.append(False)
  return False not in rc
