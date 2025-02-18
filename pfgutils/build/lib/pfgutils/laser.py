#!/usr/bin/env python

import psycopg2
import logging

from pfgutils.Settings import Database
from pfgutils.channelscache import channels
from pfgutils.connection import ecalchannels
from pfgutils.dqm.json import get, JSON2ROOT


def addLaserRun(run, valuelimit=0.1):
  connstr = "host='{0}' dbname='ecalnoise' user='{1}' password='{2}'".format(Database['options']['host'],
    Database['options']['user'], Database['options']['password'])
  ldb = psycopg2.connect(connstr)
  for sm in range(-18, 19):
    if sm == 0:
      continue
    _fillLaserRun(ldb, run, "EB", sm, valuelimit)
  for sm in range(-9, 10):
    if sm == 0:
      continue
    _fillLaserRun(ldb, run, "EE", sm, valuelimit)
  return True


def _fillLaserRun(laserdb, run, det, sm, valuelimit):
  logging.info("Run {0} det {1} SM {2}".format(run, det, sm))
  chcur = ecalchannels.cursor()
  cur = laserdb.cursor()
  dqmpath = "Ecal{1}/{0}LaserTask/Laser3/{0}LT amplitude over PN {0}{2:+03d} L3"
  dqmpath = dqmpath.format(det, ("Endcap", "Barrel")[det == "EB"], sm)
  data = get(run, dqmpath)
  if data is None:
    return False
  hist = JSON2ROOT(data)
  if det == "EB":
    for xbin in range(1, hist.GetXaxis().GetNbins() + 1):
      for ybin in range(1, hist.GetYaxis().GetNbins() + 1):
        value = hist.GetBinContent(xbin, ybin)
        if value < 0 or value > valuelimit:
          continue
        ieta = hist.GetXaxis().GetBinUpEdge(xbin)
        iphi = hist.GetYaxis().GetBinLowEdge(ybin) if sm > 0 else hist.GetYaxis().GetBinUpEdge(ybin)
        if sm < 0:
          ieta *= -1
        if iphi < 0:
          iphi *= -1
        if iphi == 0:
          iphi = 1
        dbid = channels[(ieta, iphi)]
        cur.execute("select count(*) from laser3 where dbid = %s and run = %s", (dbid, run))
        if cur.fetchone()[0] != 0:
          continue
        cur.execute("insert into laser3 values (%s, %s, %s)", (dbid, run, value))
  elif det == "EE":
    iz = 1 if sm > 0 else -1
    for xbin in range(1, hist.GetXaxis().GetNbins() + 1):
      for ybin in range(1, hist.GetYaxis().GetNbins() + 1):
        value = hist.GetBinContent(xbin, ybin)
        if value < 0 or value > valuelimit:
          continue
        ix = hist.GetXaxis().GetBinUpEdge(xbin)
        iy = hist.GetYaxis().GetBinUpEdge(ybin)
        chcur.execute("select dbid from channels where ix = ? and iy = ? and iz = ? and det = ?",
          (ix, iy, iz, "EE{0:+2d}".format(sm)))
        r = chcur.fetchone()
        if r is None:
          continue
        else:
          dbid = r[0]
        cur.execute("select count(*) from laser3 where dbid = %s and run = %s", (dbid, run))
        if cur.fetchone()[0] != 0:
          continue
        cur.execute("insert into laser3 values (%s, %s, %s)", (dbid, run, value))
  laserdb.commit()
