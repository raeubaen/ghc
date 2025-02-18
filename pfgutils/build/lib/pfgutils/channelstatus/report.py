#!/usr/bin/env python

import logging
import re

from pfgutils.connection import ecalchannels, ecalchannelstatus, oradbh
from pfgutils.misc import KnownProblems

EcalChannelStatusBits = {0: ("Channel OK", "Standard reco"),
  1: ("DAC settings problem, pedestal not in the design range", "Standard reco"),
  2: ("Channel with no laser, ok elsewhere", "Standard reco"), 3: ("Noisy", "Standard reco"),
  4: ("Very noisy", "Special reco (to be decided)"),
  8: ("Channel at fixed gain 6 (or 6 and 1)    3+5 or 3+1", "Special reco"),
  9: ("Channel at fixed gain 1     3+5 or 3+1", "Special reco"),
  10: ("Channel at fixed gain 0 (dead of type this)", "Recovery from neighbours"),
  11: ("Non responding isolated channel (dead of type other)", "Recovery from neighbours"),
  12: ("Channel and one or more neigbors not responding", "No recovery"),
  13: ("Channel in TT with no data link, TP data ok", "Recovery from TP data"),
  14: ("Channel in TT with no data link and no TP data", "None ")}


if ecalchannelstatus is None:
  logging.warning("EcalChannelStatus DB is not available")
  import sys
  sys.exit(0)

class Report:
  def __init__(self, tag, iov, subdetector):
    self.knownProblems = KnownProblems()
    self.iov = iov
    self.tag = tag
    self.det = subdetector
    self.datadbh = ecalchannelstatus
    self.datacur = self.datadbh.cursor()
    self.chdbh = ecalchannels
    self.channelcur = self.chdbh.cursor()
    self.procid = []
    self.unprocid = self.readAllChannels()
    self.report = {"TT": {}, "channels": {}}
    self.analyse()

  def readAllChannels(self):
    mask = "1%" if self.det[:2] == 'EB' else "2%"
    tmp = {}
    self.datacur.execute(
      "select dbid, status from EcalChannelStatus where iov = %s and tag = %s and dbid::text like %s",
      (self.iov, self.tag, mask))
    for k in self.datacur.fetchall():
      if int(k[1]) != 0:
        tmp.update({k[0]: int(k[1])})
    return tmp

  def analyse(self):
    for c in self.unprocid.keys():
      if c in self.procid:
        continue
      try:
        if self.det == "EB":
          ttname = "tower"
        else:
          ttname = "ccu"
        self.channelcur.execute("select det, {0} from channels where dbid = ?".format(ttname), (c,))
        (det, tower) = self.channelcur.fetchone()
      except:
        continue
      dtext = 'TT' if 'EB' in self.det else 'CCU'
      if self.isFullTT(c):
        ttname = "{0:6s} {2}{1:02d}".format(det, tower, dtext)
        self.report["TT"].update({ttname: self.getChannelStatus(c)})
        for q in self.getSameChannelsinTT(c):
          self.procid.append(q)
      else:
        if self.det == "EB":
          xy = "iphi, ieta"
        else:
          xy = "ix, iy"
        self.channelcur.execute("select {0} from channels where dbid = ?".format(xy), (c,))
        (x, y) = self.channelcur.fetchone()
        channelname = "{0:6s} {4}{1:02d} ({2:3d},{3:3d})".format(det, tower, x, y, dtext)
        self.report["channels"].update({channelname: self.getChannelStatus(c)})
        self.procid.append(c)

  def getChannelStatus(self, dbid):
    try:
      return self.unprocid[dbid]
    except:
      return None

  def getSameChannelsinTT(self, dbid):
    """ return list of channels in the same TT as dbid """
    if self.det == "EB":
      ttname = "tower"
    else:
      ttname = "ccu"
    self.channelcur.execute("select {0} , det from channels where dbid = ?".format(ttname), (dbid,))
    (tower, det) = self.channelcur.fetchone()
    self.channelcur.execute("select dbid from channels where {0}= ? and det = ?".format(ttname), (tower, det))
    return [x[0] for x in self.channelcur.fetchall()]

  def isFullTT(self, dbid):
    """ is all channels in TT have the same status ?"""
    ref = self.getChannelStatus(dbid)
    for c in self.getSameChannelsinTT(dbid):
      if self.getChannelStatus(c) != ref:
        return False
    return True

  def isMasked(self, det, tt):
    res = {"DAQ": False, "Trigger": False, "Twiki": False}
    det = det.strip()
    oradb = oradbh
    oracur = oradb.cursor()
    if "EB" in self.det:
      towername = "tower"
    else:
      towername = "ccu"
    self.channelcur.execute("select fed from channels where det = ? and {0} = ?".format(towername), (det, tt))
    fed_id = self.channelcur.fetchone()[0]
    # is masked in FE_DAQ_BAD_TT_DAT (DAQ) ?
    statussql = "select status from CMS_ECAL_CONF.FE_DAQ_BAD_TT_DAT where fed_id = {fedid} and tt_id = {ttid} and \
       rec_id = (select max(rec_id) from CMS_ECAL_CONF.FE_DAQ_BAD_TT_DAT)".format(fedid=fed_id, ttid=tt)
    status = oracur.execute(statussql).fetchone()
    if not status is None and status[0] == 1:
      res["DAQ"] = True
    # is masked in FE_CONFIG_BADTT_DAT (Trigger) !!! BEAMV6_TRANS_SPIKEKILL !!!  ?
    statussql = "select status from CMS_ECAL_CONF.FE_CONFIG_BADTT_DAT where fed_id = {fedid} and tt_id = {ttid} and \
       rec_id = (select max(rec_id) from CMS_ECAL_CONF.FE_CONFIG_BADTT_INFO where tag = 'BEAMV6_TRANS_SPIKEKILL')".format(
      fedid=fed_id, ttid=tt)
    status = oracur.execute(statussql).fetchone()
    if not status is None and status[0] == 1:
      res["Trigger"] = True
    # Check Evgueni's table
    if self.det == "EB":
      tablename = 'Problematic Trigger Towers - Barrel'
    else:
      tablename = 'Problematic FE - Endcap'
    table = self.knownProblems.getTable(tablename)[2]
    for row in table:
      if row[1] == det and int(row[3]) == int(tt):
        res["Twiki"] = True
        break
    return res

  def getBadChannels(self):
    mask = "1%" if self.det[:2] == 'EB' else "2%"
    self.datacur.execute(
      "select count(*) from EcalChannelStatus where iov = %s and status >= 8 and tag = %s and dbid::text like %s",
      (self.iov, self.tag, mask))
    badchannels = self.datacur.fetchone()[0]
    return badchannels

  def doReport(self):
    text = ""
    text += "\nh2. {0} tower/CCU statuses\n\n".format(self.det)
    headersuffix = "_. {0:18s} |_. {1:18s} |_. {2:18s} |".format("Masked in DAQ", "Masked in Trigger",
      "Evgueni's table")
    ttre = re.compile("(E[EB][+-].+) (?:TT|CCU)([0-9]+)")
    text += "\n"
    text += "|_. {0:25s} |_. Status code |".format(self.det + " towers") + headersuffix + "\n"
    for tt in sorted(self.report["TT"].keys()):
      (d, t) = ttre.findall(tt)[0]
      ismasked = self.isMasked(d, t)
      statustext = " {0:20s} | {1:20s} | {2:20s} |".format(("-", "Masked")[ismasked['DAQ']],
        ("-", "Masked")[ismasked['Trigger']], ("-", "Known")[ismasked['Twiki']])
      text += "|   {0:25s} |   {1:11d} |".format(tt, self.report["TT"][tt]) + statustext + "\n"
    text += "\nh2. {0} channel statuses\n\n".format(self.det)
    text += "|_. {0:25s} |_. Status code |\n".format(self.det + " channels")
    for c in sorted(self.report["channels"].keys()):
      text += "|   {0:25s} |   {1:11d} |\n".format(c, self.report['channels'][c])
    text += "\n"
    return text


def getReport(tag, iov):
  dbh = ecalchannelstatus
  cdbh = dbh.cursor()
  text = ""

  knownProblems = KnownProblems()

  reportEB = Report(tag, iov, "EB")
  reportEEp = Report(tag, iov, "EE+")
  reportEEm = Report(tag, iov, "EE-")

  text += "\nh2. Active channels\n\n"
  text += "EB  : {0:03.3f}%\n".format((61200 - reportEB.getBadChannels()) * 100.0 / 61200)
  text += "EE  : {0:03.3f}%\n".format((14648 - reportEEp.getBadChannels()) * 100.0 / 14648)

  text += "\nh2. Statuses\n\n"
  text += "|_. {0:15s} |_. {1:80s} |_. {2:30s} |\n".format("Status", "Description", "Reco action")
  for r in sorted(EcalChannelStatusBits.keys()):
    text += "|   {0:15d} |   {1:80s} |   {2:30s} |\n".format(r, EcalChannelStatusBits[r][0],
      EcalChannelStatusBits[r][1])
  text += "\n"

  text += "\nh2. Status summary for IOV {0}\n\n".format(iov)
  text += "|_. {0:15s} |_. {1:5s} |_. {2:5s} |\n".format("Status", "EB", "EE")
  for i in range(1, 15):
    count = {'EB': 0, 'EE': 0}
    for d in ['EB', 'EE']:
      #    try:
      mask = "1%" if d == 'EB' else "2%"
      cdbh.execute(
        "select count(*) from EcalChannelStatus where iov = %s and status = %s and tag = %s and dbid::text like %s",
        (iov, i, tag, mask))
      count[d] = cdbh.fetchone()[0]
      #    except:
      #      count[d] = 0
    text += "|   {0:15d} |   {1:5d} |   {2:5d} |\n".format(i, count["EB"], count['EE'])

  for d in ['EB', 'EE']:
    try:
      mask = "1%" if d == 'EB' else "2%"
      cdbh.execute(
        "select count(*) from EcalChannelStatus where iov = %s and status > 14 and tag = %s and dbid::text like %s".format(
          d), (iov, tag, mask))
      count[d] = cdbh.fetchone()[0]
    except:
      count[d] = 0
  text += "|   {0:15s} |   {1:5d} |   {2:5d} |\n".format(">14", count["EB"], count['EE'])

  for k in (reportEB, reportEEp, reportEEm):
    k.knownProblems = knownProblems
    text += k.doReport()
  return text
