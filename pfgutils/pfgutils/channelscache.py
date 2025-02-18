#/usr/bin/env python

from pfgutils.connection import ecalchannels

channels = {}

cc = ecalchannels.cursor()
cc.execute("select dbid, ieta, iphi, ix, iy, iz from channels")
for row in cc.fetchall():
  if row['ieta'] != -999:
    channels[(row['ieta'], row['iphi'])] = row['dbid']
  if row['ix'] != -999:
    channels[(row['ix'], row['iy'], row['iz'])] = row['dbid']
del cc
