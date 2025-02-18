#!/usr/bin/env python

import logging

from pfgutils.connection import ecalchannelstatus, ecalchannels
import pfgutils.textile


def getChannelName(cur, dbid):
  det = "EB" if str(dbid)[0] == "1" else "EE"
  if det == "EB":
    ttname = "tower"
    xy = "iphi, ieta"
  else:
    ttname = "ccu"
    xy = "ix, iy"
  cur.execute("select det, {0}, {1} from channels where dbid = ?".format(ttname, xy), (dbid,))
  (det, tower, x, y) = cur.fetchone()
  return "{det} {ttname}{tt} {xyr}".format(det=det, ttname="CCU", tt=tower, xyr=str([x, y]))


def compare(tag1, iov1, tag2, iov2):
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return ""
  header = ["Channel", "IOV {0} ({1})".format(iov1, tag1), "IOV {0} ({1})".format(iov2, tag2)]
  tableb = []
  dbh = ecalchannelstatus.cursor()
  cdb = ecalchannels.cursor()
  out = pfgutils.textile.hn("Differences between IOVs {0} and {1}".format(iov1, iov2), 2)
  # EB
  sql = "select t1.dbid from EcalChannelStatus as t1 inner join EcalChannelStatus as t2 on t1.dbid = t2.dbid where t1.iov = %s \
      and t2.iov = %s and t1.status != t2.status and t1.tag = %s and t2.tag = %s"
  dbh.execute(sql, (iov1, iov2, tag1, tag2))

  for dbid in [x[0] for x in dbh.fetchall()]:
    dbh.execute('select status from EcalChannelStatus where iov = %s and dbid = %s and tag = %s', (iov1, dbid, tag1))
    old = dbh.fetchone()[0]
    dbh.execute('select status from EcalChannelStatus where iov = %s and dbid = %s and tag = %s', (iov2, dbid, tag2))
    new = dbh.fetchone()[0]
    tableb.append((getChannelName(cdb, dbid), old, new))

  sql = "select distinct dbid from EcalChannelStatus where iov = %s and tag = %s and \
    dbid not in (select distinct dbid from EcalChannelStatus where iov = %s and tag = %s)"
  dbh.execute(sql, (iov1, tag1, iov2, tag2))
  for dbid in [x[0] for x in dbh.fetchall()]:
    dbh.execute("select status from EcalChannelStatus where iov = %s and dbid = %s and tag = %s", (iov1, dbid, tag1))
    tableb.append((getChannelName(cdb, dbid), dbh.fetchone()[0], '0'))

  sql = "select distinct dbid from EcalChannelStatus where iov = %s and tag = %s and dbid not in (select distinct dbid from EcalChannelStatus where iov = %s and tag = %s)"
  dbh.execute(sql, (iov2, tag2, iov1, tag1))
  for dbid in [x[0] for x in dbh.fetchall()]:
    dbh.execute("select status from EcalChannelStatus where iov = %s and dbid = %s and tag = %s", (iov2, dbid, tag2))
    tableb.append((getChannelName(cdb, dbid), "0", dbh.fetchone()[0]))
  out += pfgutils.textile.table(header, tableb)
  return out
