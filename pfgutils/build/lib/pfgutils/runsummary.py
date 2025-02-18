#!/usr/bin/env python

from .connection import oradbh
from .oracle import rows_as_dicts


class RunSummary:
  cache = {}

  def __init__(self):
    ocur = oradbh.cursor()
    self.ocur = ocur

  @staticmethod
  def getValueFromDict(data, column='*'):
    if column == '*':
      return data
    else:
      if column in data:
        return data[column]
      else:
        raise RuntimeError("No such column '{0}'".format(column))

  def getRunInfo(self, run, column='*'):
    if run in self.cache:
      return self.getValueFromDict(self.cache[run], column)
    self.ocur.execute("select * from CMS_WBM.RUNSUMMARY where runnumber = :1", (run,))
    res = [x for x in rows_as_dicts(self.ocur)]
    if len(res) == 0:
      return None
    else:
      self.cache[run] = res[0]
      return self.getRunInfo(run, column)

  def getBField(self, run):
    return self.getRunInfo(run, 'BFIELD')
