#!/usr/bin/env python

import os
import sys
import logging

import pfgutils.cmssw
import pfgutils.plotECAL
import pfgutils.webhelpers
from .report import getReport


def getdirpath(tag, iov, field):
  dirpath = os.path.join("payloads", tag, str(iov), field)
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)
  return dirpath


def main():
  tag, iov, field = sys.argv[2:5]
  iov = int(iov)
  dirpath = getdirpath(tag, iov, field)
  rootfile = os.path.join(dirpath, "output.root")
  pngfile = os.path.join(dirpath, "output.png")
  if os.path.exists(rootfile) and os.path.exists(pngfile):
    return dirpath
  update()
  return dirpath


def update(cwd = '.'):
  if os.path.exists(cwd):
    os.chdir(cwd)
  else:
    logging.warning("Directory {0} not found".format(dirpath))
  tags = pfgutils.webhelpers.getTagsInDB()
  for tag in tags:
    fields = pfgutils.webhelpers.getFieldsInDB(tag)
    iovs = pfgutils.webhelpers.getIOVInDB(tag)
    toprocess = {}
    for iov in iovs:
      for field in fields:
        dirpath = getdirpath(tag, iov, field)
        rootfile = os.path.join(dirpath, "output.root")
        pngfile = os.path.join(dirpath, "output.png")
        if not os.path.exists(rootfile) or not os.path.exists(pngfile):
          if iov not in toprocess:
            toprocess[iov] = []
          toprocess[iov].append(field)
    for iov in list(toprocess.keys()):
      data = pfgutils.cmssw.getPayload(iov, tag)
      #      open(tag+str(iov), 'w').write(json.dumps(data, indent=1))
      for field in toprocess[iov]:
        logging.info("{0} {1} {2} ...".format(tag, iov, field))
        dirpath = getdirpath(tag, iov, field)
        rootfile = os.path.join(dirpath, "output.root")
        pngfile = os.path.join(dirpath, "output.png")
        vals = []
        for dbid in data.keys():
          vals.append((dbid, data[dbid][field]))
        values = {'name': "{0}".format(tag), 'title': "{0} {1} {2}".format(tag, iov, field), 'values': vals}
        # special rules for EcalChannelStatus
        if "EcalChannelStatus" in tag:
          values['maximum'] = 14
          values['minimum'] = 0
          vals = [x for x in vals if x[1] != 0]
          values['values'] = vals
          logfile = os.path.join(dirpath, "report.log")
          with open(logfile, 'w') as f:
            f.write(getReport(tag, iov))
          #        open(tag + str(iov) + field, 'w').write(json.dumps(values, indent = 1))
        canvas = pfgutils.plotECAL.getCanvasDbIds(values)
        canvas.SetName("canvas")
        canvas.SetTitle("canvas")
        canvas.SaveAs(rootfile)
        canvas.SaveAs(pngfile)
        logging.info("Done")


if __name__ == "__main__":
  main()
