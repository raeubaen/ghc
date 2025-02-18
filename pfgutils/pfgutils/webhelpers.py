#!/usr/bin/env python

import os
import logging

from pfgutils.connection import ecalchannelstatus


def getTagsInDB():
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return []
  cur = ecalchannelstatus.cursor()
  cur.execute("select tag from tags")
  return sorted([x[0] for x in cur.fetchall()])


def getIOVInDB(tag):
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return []
  cur = ecalchannelstatus.cursor()
  cur.execute("select tagid from tags where tag = %s", (tag,))
  tagid = cur.fetchone()[0]
  cur.execute("select iov from iovs where tagid = %s group by iov", (tagid,))
  return sorted([x[0] for x in cur.fetchall()])


def getFieldsInDB(tag):
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return []
  cur = ecalchannelstatus.cursor()
  cur.execute("select tagid from tags where tag = %s", (tag,))
  tagid = cur.fetchone()[0]
  cur.execute("select fieldid from iovs where tagid = %s group by fieldid", (tagid,))
  fieldids = [x[0] for x in cur.fetchall()]
  res = []
  for fieldid in fieldids:
    cur.execute("select field from fields where fieldid = %s", (fieldid,))
    res.append(cur.fetchone()[0])
  return sorted(res)


def getSVGFromCanvas(canvas):
  import subprocess
  p = subprocess.Popen(['mktemp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = p.communicate()
  filename = stdout.strip() + ".svg"
  canvas.SaveAs(filename)
  with open(filename, 'r') as f:
    text = f.read()
  os.remove(filename)
  return text
