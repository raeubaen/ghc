#!/usr/bin/env python
import ROOT
import json
import os
import logging

import psycopg2

from pfgutils.Settings import Database, rootpath
from pfgutils.connection import dqms, ecalchannels
from pfgutils.dqm.json import get, JSON2ROOT
from pfgutils.misc import download
from pfgutils.channelscache import channels


def addNoiseRun(jsonfile, usejson=False):
  conn_string = "host='{host}' dbname='{dbname}' user='{user}' password='{password}'".format(
    host=Database['options']['host'], dbname="ecalnoise", user=Database['options']['user'],
    password=Database['options']['password'], )
  ndb = psycopg2.connect(conn_string)
  cur = ndb.cursor()

  with open(jsonfile, 'r') as f:
    try:
      requesteddata = json.loads(f.read())
    except:
      logging.error("Cannot load json!")
      return False
  for dataset in list(requesteddata.keys()):
    cur.execute("select id from datasets where dataset = %s", (dataset,))
    datasetid = cur.fetchone()
    if datasetid is None:
      cur.execute("insert into datasets (dataset) values (%s)", (dataset,))
      cur.execute("select id from datasets where dataset = %s", (dataset,))
      datasetid = cur.fetchone()[0]
      ndb.commit()
    else:
      datasetid = datasetid[0]
    cur.execute("select run from noise where datasetid = %s group by run", (datasetid,))
    runs = [x[0] for x in cur.fetchall()]
    if len(runs) != 0:
      rs = [y for y in requesteddata[dataset] if y not in runs]
    else:
      rs = requesteddata[dataset]
    for run in rs:
      # EB
      det = "EB"
      for sm in range(-18, 19):
        if sm == 0:
          continue
        _fillNoiseRun(ndb, run, det, sm, dataset, datasetid, usejson)
      # EE
      det = "EE"
      for sm in range(-9, 10):
        if sm == 0:
          continue
        _fillNoiseRun(ndb, run, det, sm, dataset, datasetid, usejson)
  return True


def _fillNoiseRun(noisedb, run, det, sm, dataset, datasetid, usejson=False):
  logging.info("Run {0} det {1} SM {2} dataset {3}".format(run, det, sm, dataset))
  cur = noisedb.cursor()
  if usejson:
    meandqmpath = "Ecal{1}/{0}PedestalOnlineTask/Gain12/{0}POT pedestal {0}{2:+03d} G12"
    rmsdqmpath = "Ecal{1}/{0}PedestalOnlineClient/{0}POT pedestal rms map G12 {0}{2:+03d}"
    meandqmpath = meandqmpath.format(det, ("Endcap", "Barrel")[det == "EB"], sm)
    rmsdqmpath = rmsdqmpath.format(det, ("Endcap", "Barrel")[det == "EB"], sm)
    rmsdata = get(run, rmsdqmpath, dataset)
    meandata = get(run, meandqmpath, dataset)
    if rmsdata is None or meandata is None:
      return False
    rmshist = JSON2ROOT(rmsdata)
    meanhist = JSON2ROOT(meandata)
  else:
    if dataset == "online":
      d = dqms['online']
    else:
      d = dqms['offline']
    files = [x[1] for x in d.getFilesInDataset(run, dataset)]
    if len(files) == 0:
      logging.error("No files found in DQM ROOT area")
      return False
    else:
      url = files[0]
    tmppath = os.path.join(rootpath, os.path.basename(url))
    if not download(url, tmppath):
      return False
    f = ROOT.TFile(tmppath)
    meandqmpath = "/DQMData/Run {3}/Ecal{1}/Run summary/{0}PedestalOnlineTask/Gain12/{0}POT pedestal {0}{2:+03d} G12"
    rmsdqmpath = "/DQMData/Run {3}/Ecal{1}/Run summary/{0}PedestalOnlineClient/{0}POT pedestal rms map G12 {0}{2:+03d}"
    meandqmpath = meandqmpath.format(det, ("Endcap", "Barrel")[det == "EB"], sm, run)
    rmsdqmpath = rmsdqmpath.format(det, ("Endcap", "Barrel")[det == "EB"], sm, run)
    rmshist = f.Get(rmsdqmpath)
    meanhist = f.Get(meandqmpath)
  getxup = rmshist.GetXaxis().GetBinUpEdge
  getyup = rmshist.GetYaxis().GetBinUpEdge
  getylow = rmshist.GetYaxis().GetBinLowEdge
  if det == "EB":
    for ix in range(1, rmshist.GetXaxis().GetNbins() + 1):
      for iy in range(1, rmshist.GetYaxis().GetNbins() + 1):
        rmsvalue = rmshist.GetBinContent(ix, iy)
        meanvalue = meanhist.GetBinContent(ix, iy)
        ieta = getxup(ix)
        iphi = getylow(iy) if sm > 0 else getyup(iy)
        if sm < 0:
          ieta *= -1
        if iphi < 0:
          iphi *= -1
        if iphi == 0:
          iphi = 1
        dbid = channels[(ieta, iphi)]
        if rmsvalue < -1:
          rmsvalue = -1
        if meanvalue < -1:
          meanvalue = -1
        cur.execute("insert into noise (dbid, run, datasetid, rms, mean) values (%s, %s, %s, %s, %s)",
          (dbid, run, datasetid, rmsvalue, meanvalue))
  elif det == "EE":
    chcur = ecalchannels.cursor()
    iz = 1 if sm > 0 else -1
    for ix in range(1, rmshist.GetXaxis().GetNbins() + 1):
      for iy in range(1, rmshist.GetYaxis().GetNbins() + 1):
        rmsvalue = rmshist.GetBinContent(ix, iy)
        meanvalue = meanhist.GetBinContent(ix, iy)
        x = getxup(ix)
        y = getyup(iy)
        if rmsvalue == 0 or rmsvalue < -1:
          continue
        if meanvalue == 0 or meanvalue < -1:
          continue
        chcur.execute("select dbid from channels where ix = ? and iy = ? and iz = ? and det = ? ",
          (x, y, iz, "EE{0:+2d}".format(sm)))
        r = chcur.fetchone()
        if r is None:
          continue
        dbid = r[0]
        cur.execute("insert into noise (dbid, run, datasetid, rms, mean) values (%s, %s, %s, %s, %s)",
          (dbid, run, datasetid, rmsvalue, meanvalue))
  noisedb.commit()
