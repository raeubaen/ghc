# !/usr/bin/env python

import os
import shutil
import subprocess
import logging

from pfgutils.Settings import tmpdir
from pfgutils.connection import ecalchannelstatus
from pfgutils.misc import gettmp


def parsePayload(text):
  import xml.etree.ElementTree
  from pfgutils.connection import ecalchannels
  cur = ecalchannels.cursor()
  if "</boost_serialization>" not in text:
    text += "</boost_serialization>"
  tree = xml.etree.ElementTree.fromstring(text)
  cmsCondPayload = tree.getchildren()[0]
  if 'eb-' not in [x.tag for x in cmsCondPayload.getchildren()]:
    cmsCondPayload = cmsCondPayload.getchildren()[0]
  eb, ee = cmsCondPayload.getchildren()
  ebitems = [xlam for xlam in eb.getchildren()[0].getchildren() if xlam.tag == 'item']
  eeitems = [xlam for xlam in ee.getchildren()[0].getchildren() if xlam.tag == 'item']
  result = {}
  # eb
  hashedid = 0
  for item in ebitems:
    cur.execute("select dbid from channels where hashedid = ? and det like ?", (hashedid, 'EB%'))
    dbid = cur.fetchone()[0]
    values = {}
    for f in item.getchildren():
      fname = f.tag.replace('-', '').replace('+', '')
      try:
        value = float(f.text)
        values[fname] = value
      except Exception as e:
        logging.error("Error:" + str(e))
    result[dbid] = values
    hashedid += 1
  # eb
  hashedid = 0
  for item in eeitems:
    cur.execute("select dbid from channels where hashedid = ? and det like ?", (hashedid, 'EE%'))
    dbid = cur.fetchone()[0]
    values = {}
    for f in item.getchildren():
      fname = f.tag.replace('-', '').replace('+', '')
      try:
        value = float(f.text)
        values[fname] = value
      except Exception as e:
        logging.error("Error:" + str(e))
    result[dbid] = values
    hashedid += 1
  return result


def dumpPayload(iov, tag, data):
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return
  cur = ecalchannelstatus.cursor()
  try:
    cur.execute("select tagid from tags where tag = %s", (tag,))
    r = cur.fetchone()
    if r is None:
      cur.execute("insert into tags (tag) values (%s)", (tag,))
      cur.execute("select tagid from tags where tag = %s", (tag,))
      r = cur.fetchone()
    tagid = r[0]
    for dbid in data.keys():
      dbid = int(dbid)
      for field in data[dbid].keys():
        cur.execute("select fieldid from fields where field = %s", (field,))
        r = cur.fetchone()
        if r is None:  # fieldid not found
          cur.execute("insert into fields (field) values (%s)", (field,))
          cur.execute("select fieldid from fields where field = %s", (field,))
          r = cur.fetchone()
        fieldid = r[0]
        value = float(data[dbid][field])
        cur.execute("insert into payloads values (%s, %s, %s, %s, %s)", (iov, tagid, fieldid, value, dbid))
    cur.execute("refresh materialized view iovs")
    if "EcalChannelStatus" in tag:
      cur.execute("refresh materialized view ecalchannelstatus")
  except Exception as e:
    ecalchannelstatus.rollback()
    raise RuntimeError("ERROR: " + str(e))
  else:
    ecalchannelstatus.commit()


def _loadPayload(iov, tag):
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return
  cur = ecalchannelstatus.cursor()
  cur.execute("select tagid from tags where tag = %s", (tag,))
  r = cur.fetchone()
  if r is None:
    logging.warning("Not tag '{0}' found".format(tag))
    return {}
  tagid = r[0]
  cur.execute(
    "select dbid, field, value from payloads inner join fields on (payloads.fieldid = fields.fieldid) where iov = %s and tagid = %s",
    (iov, tagid))
  result = {}
  for dbid, field, value in cur.fetchall():
    if dbid not in result:
      result[dbid] = {}
    result[dbid][field] = value
  return result


def checkPayload(iov, tag):
  # check if data in DB
  if ecalchannelstatus is None:
    logging.warning("EcalChannelStatus DB is not available")
    return
  iov = int(iov)
  cur = ecalchannelstatus.cursor()
  cur.execute("select tagid from tags where tag = %s", (tag,))
  r = cur.fetchone()
  if r is None:
    return False
  tagid = r[0]
  cur.execute("select dbid from payloads where iov = %s and tagid = %s limit 1", (iov, tagid))
  if cur.fetchone() is None:
    return False
  return True


def getPayload(iov, tag):
  if checkPayload(iov, tag):
    return _loadPayload(iov, tag)
  cmssw = CMSSW()
  data = parsePayload(cmssw.dumpIOV(iov, tag))
  dumpPayload(iov, tag, data)
  return data


class CMSSW:
  def __init__(self, CMSSW_VERSION='CMSSW_7_4_7', platform='slc6_amd64_gcc491'):
    self.cmssw_version = CMSSW_VERSION
    self.tmppath = gettmp(True)
    self.path = os.path.join(self.tmppath, self.cmssw_version)
    if not os.path.exists(self.path):
      os.mkdir(self.path)
    os.environ['SCRAM_ARCH'] = platform
    os.environ['CMS_PATH'] = '/cvmfs/cms.cern.ch'
    os.environ['PATH'] = ':'.join(['/cvmfs/cms.cern.ch/common:/cvmfs/cms.cern.ch/bin'] + os.environ['PATH'].split(':'))
    os.environ['TMP'] = tmpdir
    self._initCMSSW()

  def __del__(self):
    shutil.rmtree(self.tmppath)

  def _initCMSSW(self):
    cmd = "cd {0}; scram project {1}".format(self.tmppath, self.cmssw_version)
    rc = True if os.system(cmd) == 0 else False
    if not rc:
      return rc
    p = subprocess.Popen(['scramv1', 'runtime', '-sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.path)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
      logging.error("Cannot prepare enviroment for {0} in {1}".format(self.cmssw_version, self.path))
      logging.error(stderr)
      return False
    # prepare export list
    for line in [x.strip() for x in stdout.strip().split('\n')]:
      key = line.split()[1].split('=')[0]
      value = line.split()[1].split('=')[1].replace('"', '').replace("'", "")
      key = key.strip()
      value = value.strip()
      if value[-1] == ';':
        value = value[:-1]
      os.environ[key] = value

  def execCmd(self, cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=self.path)
    stdout, stderr = p.communicate()
    return p.returncode, stdout.strip(), stderr.strip()

  def getIOVs(self, tag):
    ret = self.execCmd('conddb list {0}'.format(tag))
    if ret[0] != 0:
      logging.warning("Tag {0} not found".format(tag))
      return []
    stdout = ret[1]
    iovs = []
    for line in [x.strip() for x in stdout.strip().split('\n')[2:] if x.strip() != ""]:
      a = [x.strip() for x in line.split()]
      iovs.append((int(a[0]), a[1] + " " + a[2], a[3], a[4]))
    return iovs

  def dumpIOV(self, iov, tag):
    hashstr = [x[2] for x in self.getIOVs(tag) if x[0] == iov]
    if len(hashstr) == 0:
      logging.warning("No hash found for IOV {0} and tag {1}".format(iov, tag))
      return False
    hashstr = hashstr[0]
    rec = self.execCmd('conddb dump {0}'.format(hashstr))
    if rec[0] != 0:
      logging.error("Dump from CMSSW failed.")
      logging.error(rec[2])
      return False
    return rec[1]

  def listTags(self):
    a = self.execCmd("conddb listTags")[1]
    return [x.split()[0] for x in a.split('\n')[2:]]
