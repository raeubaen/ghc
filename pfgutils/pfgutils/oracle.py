#!/usr/bin/env python

import logging
from .connection import oradbh

_lhcstatuses = []


def getTable(table, view=None):
  """ Dump Oracle table """
  sql = "select COLUMN_NAME from ALL_TAB_COLUMNS where TABLE_NAME='{0}'".format(table)
  headers = [i[0] for i in oradbh.cursor().execute(sql)]
  if view:
    view += '.'
  else:
    view = ""
  sql = "select * from {0}{1} where rec_id = (select max(rec_id) from {0}{1})".format(view, table)
  data = [list(i) for i in oradbh.cursor().execute(sql)]
  return table, headers, data


## useful functions to extract data from Oracle Database

def rows_as_dicts(cursor):
  """ returns cx_Oracle rows as dicts """
  colnames = [i[0] for i in cursor.description]
  for row in cursor:
    yield dict(list(zip(colnames, row)))


def getLHCFILL(lhcfill):
  """
  Return dict with ghcfill data
  """
  ocur = oradbh.cursor()
  ocur.execute("select * from CMS_RUNTIME_LOGGER.RUNTIME_SUMMARY where lhcfill = :fill", fill=lhcfill)
  return next(rows_as_dicts(ocur))


def getAllLHCFILL():
  """
  Return list of all LHCFILLs
  """
  ocur = oradbh.cursor()
  ocur.execute("select lhcfill from CMS_RUNTIME_LOGGER.RUNTIME_SUMMARY where lhcfill is not NULL order by lhcfill desc")
  return [x[0] for x in ocur.fetchall()]


def getDowntimes(lhcfill):
  """
  Return list of (runnumber, id) of downtimes for given lhcfill
  """
  ocur = oradbh.cursor()
  sql = "select * from CMS_RUNTIME_LOGGER.DOWNTIME_EVENTS where runtime_id = (select id from CMS_RUNTIME_LOGGER.RUNTIME_SUMMARY where lhcfill = :lhcfill)"
  ocur.execute(sql, lhcfill=lhcfill)
  return [x for x in rows_as_dicts(ocur)]


def getLumisections(run):
  ocur = oradbh.cursor()
  ocur.execute("select * from CMS_RUNTIME_LOGGER.LUMI_SECTIONS where runnumber = :run", run=run)
  return [x for x in rows_as_dicts(ocur)]


def getLumisectionInDowntime(downtimedict):
  """
  Return delivered and live luminosity for given downtime
  """
  ocur = oradbh.cursor()
  sql = "select max(delivlumi) - min(delivlumi) from CMS_RUNTIME_LOGGER.LUMI_SECTIONS where  \
    STARTTIME >= (select downtime from CMS_RUNTIME_LOGGER.DOWNTIME_EVENTs where runnumber = :run and cat_id = :catid and id = :did) \
    and starttime <= (select uptime from CMS_RUNTIME_LOGGER.DOWNTIME_EVENTs where runnumber = :run and cat_id = :catid and id = :did)"
  ocur.execute(sql, run=downtimedict['RUNNUMBER'], catid=downtimedict['CAT_ID'], did=downtimedict['ID'])
  r = ocur.fetchone()
  if r is not None:
    return r[0]
  return r


def getRuntimeTypes():
  ocur = oradbh.cursor()
  ocur.execute("select * from CMS_RUNTIME_LOGGER.RUNTIME_TYPE")
  return [x for x in rows_as_dicts(ocur)]


def getLHCStatuses():
  global _lhcstatuses
  if len(_lhcstatuses) != 0:
    return _lhcstatuses
  ocur = oradbh.cursor()
  ocur.execute("select * from CMS_LHC_BEAM_COND.LHC_BEAMMODE order by diptime asc")
  _lhcstatuses = [x for x in rows_as_dicts(ocur)]
  return _lhcstatuses


def getLHCStatusForRun(run):
  from . import runsummary
  rs = runsummary.RunSummary()
  runstart = rs.getRunInfo(run, "STARTTIME")
  runend = rs.getRunInfo(run, "STOPTIME")
  if runend is None:
    import datetime
    runend = datetime.datetime.now()
  lhcstatuses = getLHCStatuses()
  statuses = []
  for sti in range(len(lhcstatuses)):
    st = lhcstatuses[sti]
    try:
      nextst = lhcstatuses[sti + 1]
    except:
      if st['DIPTIME'] <= runend:
        statuses.append(st)
      continue
    if st['DIPTIME'] <= runstart and nextst['DIPTIME'] <= runstart:
      continue
    elif st['DIPTIME'] >= runend:
      continue
    else:
      statuses.append(st)
  return sorted([(x['VALUE'], x['DIPTIME']) for x in statuses], key=lambda xlam: xlam[1])


def getTCDSFreqMonVDiff(run):
  ocur = oradbh.cursor()
  from . import runsummary
  rs = runsummary.RunSummary()
  runstart = rs.getRunInfo(run, "STARTTIME")
  runend = rs.getRunInfo(run, "STOPTIME")
  sql = "select max(frequency) - min(frequency) from CMS_TCDS_MONITORING.TCDS_FREQMON_V where timestamp between :1 and :2"
  ocur.execute(sql, (runstart, runend))
  r = ocur.fetchone()
  if r is not None:
    return r[0]
  return r


def getFEDStatus(run):
  sql = "select string_value from CMS_RUNINFO.RUNSESSION_PARAMETER where runnumber = :1 and name = :2"
  ocur = oradbh.cursor()
  ocur.execute(sql, (run, "CMS.LVL0:FED_ENABLE_MASK"))
  res = ocur.fetchone()
  if res is None:
    return None
  res = res[0].strip()
  if len(res) == 0:
    return {}
  fedlist = res.split('%')
  result = {}
  for pair in fedlist:
    if '&' not in pair:
      continue
    fed, status = pair.split('&') 
    fed = int(fed)
    if status == '':
      status = 0
    status = 1 if int(status) != 0 else 0
    result[fed] = status
  return result


def getExcludedFEDs(run):
  st = getFEDStatus(run)
  return [x for x in st if st[x] == 0]


def getEnabledFEDs(run):
  st = getFEDStatus(run)
  return [x for x in st if st[x] != 0]
