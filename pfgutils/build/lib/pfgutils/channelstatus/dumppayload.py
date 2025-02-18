#!/usr/bin/env python

import sys

import pfgutils.cmssw
from pfgutils.channelstatus.update import update


def run(tag='EcalChannelStatus_v1_hlt', iovs='all', runsnewer=247000):
  cmssw = pfgutils.cmssw.CMSSW()
  print("TAG:", tag)
  if iovs == "all":
    iovs = [x[0] for x in cmssw.getIOVs(tag) if x[0] > runsnewer]
  print("All IOVs: ", iovs)
  iovs = [xlam for xlam in iovs if not pfgutils.cmssw.checkPayload(xlam, tag)]
  print("IOVs to process: ", iovs)
  for iov in iovs:
    iov = int(iov)
    print(tag, iov)
    data = pfgutils.cmssw.parsePayload(cmssw.dumpIOV(iov, tag))
    pfgutils.cmssw.dumpPayload(iov, tag, data)
  print("Done")
  print("Updating web cache in .../payloads/")
  update()


if __name__ == "__main__":
  if len(sys.argv) == 2:
    run(sys.argv[1])
  elif len(sys.argv) > 2:
    run(sys.argv[1], sys.argv[2])
  else:
    print("{0} tag iov|all".format(__file__))
    
