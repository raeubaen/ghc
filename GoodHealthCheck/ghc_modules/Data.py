#!/usr/bin/env python
import inspect
import itertools
import logging
import sys
from collections import defaultdict

from collections.abc import Iterable

import sqlite3

import psycopg2

import pfgutils.connection
from pfgutils import Settings

# chdb = pfgutils.connection.ecalchannels
# cur_chdb = chdb.cursor()

logger = logging.getLogger()


class Data(object):
  """
    Basic class for Data obtained from detector
  """
  PEDESTAL_FLAGS = ['DP', 'BP', 'LR', 'VLR']
  HV_FLAGS = ['BV']
  TESTPULSE_FLAGS = ['DTP', 'STP', 'LTP']
  LASER_FLAGS = ['DLAMPL', 'SLAMPL', 'LLERRO']

  def __init__(self, ghc_id, keep):

    self.dbh = conn = sqlite3.connect("database.db")

    '''
    psycopg2.connect(
      "host='{host}' dbname='ecalghc' user='{user}' password='{password}'".format(
        host=Settings.Database['options']['host'],
        user=Settings.Database['options']['user'],
        password=Settings.Database['options']['password'],
      ))
    '''

    self.cur = self.dbh.cursor()

    self.cur.execute(f"SELECT ghc FROM ghc WHERE ghc_id={ghc_id}")
    res = self.cur.fetchone()
    if res is not None:
      self.ghc_id = res[0]
      self.can_redo = True
    else:
      self.cur.execute("INSERT INTO ghc (ghc_id) VALUES (%s)", (ghc_id,))
      self.cur.execute("SELECT ghc FROM ghc WHERE ghc_id=%s", (ghc_id,))
      self.ghc_id = self.cur.fetchone()[0]
      self.can_redo = False
      self.dbh.commit()

    self.keep_bad = keep
    self.masked_channels = None

    self._has_ped_hvon = None
    self._has_ped_hvoff = None
    self._has_testpulse = None
    self._has_laser = None

    self.updateEcalChannelFlags()

  def updateEcalChannelFlags(self):
#
#    logger.info("Getting list of masked ecal channels")
#    dbhst = psycopg2.connect(
#      "host='{host}' dbname='ecalchannelstatus' user='{user}' password='{password}'".format(
#        host=Settings.Database['options']['host'],
#        user=Settings.Database['options']['user'],
#        password=Settings.Database['options']['password'],
#      ))
#
#    curst = dbhst.cursor()
#
#    curst.execute("SELECT dbid FROM ecalchannelstatus WHERE status > %s and \
#      iov = (select max(iov) from ecalchannelstatus) and tag=%s",
#                  (Settings.max_good_status, 'EcalChannelStatus_v1_hlt'))
#
    self.masked_channels = () #tuple(c[0] for c in curst)

  @staticmethod
  def getAllChannels(det='ALL'):
    """
      Return list of all channels
    """
    cur_chdb = pfgutils.connection.ecalchannels.cursor()
    if pfgutils.connection.ecalchannelsdb != "sqlite3":
        cur_chdb.execute("SELECT dbid FROM channels WHERE dbid::text  LIKE %s", (det_to_sql(det),))
    else:
        cur_chdb.execute("SELECT dbid FROM channels WHERE dbid LIKE ?", (det_to_sql(det),))
    return [c['dbid'] for c in cur_chdb]

  @staticmethod
  def getNumOfAllChannels(det='ALL'):
    """
      Return number of channels in a given subdetector
    """
    cur_chdb = pfgutils.connection.ecalchannels.cursor()
    if pfgutils.connection.ecalchannelsdb != "sqlite3":
        cur_chdb.execute("SELECT COUNT(dbid) FROM channels WHERE dbid::text LIKE %s", (det_to_sql(det),))
    else:
        cur_chdb.execute("SELECT COUNT(dbid) FROM channels WHERE dbid LIKE ?", (det_to_sql(det),))
    return list(cur_chdb.fetchone().values())[0]

  @property
  def isClassified(self):
    self.cur.execute("SELECT classified FROM ghc WHERE ghc=%s", (self.ghc_id,))
    return self.cur.fetchone()[0]

  @isClassified.setter
  def isClassified(self, x):
    assert isinstance(x, bool)
    self.cur.execute("UPDATE ghc SET classified=%s WHERE ghc=%s", (x, self.ghc_id))

  def isMasked(self, dbid):
    if self.keep_bad:
      return False

    db_id = int(dbid)

    return db_id in self.masked_channels

  def getNumOfInactiveChannels(self, det, datatype=None):
    """
      Returns number of inactive channels
    """
    if not self.have_datatype(datatype):
      return 0

    return self.getNumOfAllChannels(det=det) - self.getNumOfActiveChannels(det=det, datatype=datatype)

  def getInactiveChannels(self, det, datatype=None):
    """
    Returns list of inactive channel
    :param det: subdetector
    :param datatype: data type
    :return: tuple
    """
    if datatype is not None and not self.have_datatype(datatype):
      return tuple()

    return tuple(set(self.getAllChannels(det=det)) - set(self.getActiveChannels(det=det, datatype=datatype)))

  def getNumOfDesignChannels(self):
    self.classifyChannels()

    n = self.getNumChannelsWithFlag(('BPG12', 'DPG12', 'VLRG12', 'LRG12'), exp='or', det='ALL')
    return self.getNumOfActiveChannels(det='ALL') - n

  def getDesignChannels(self):
    self.classifyChannels()

    flagged = self.getChannelsWithFlag(('BPG12', 'DPG12', 'VLRG12', 'LRG12'), exp='or', det='ALL')
    all_ = self.getActiveChannels(det='ALL')
    res = tuple(set(all_) - set(flagged))
    # logger.debug("Flagged %d, All %d, res %d", len(flagged), len(all_), len(res))

    return res

  def getProblematicChannels(self, without_missing=False):
    self.classifyChannels()
    if without_missing:
      filter_sql = "AND NOT flags.dbid IN (SELECT dbid FROM missed_channels WHERE ghc=%(ghc)s)"
    else:
      filter_sql = ""

    # if not self.keep_bad:
    #      filter_sql += " AND (SELECT status FROM channelstatus WHERE channelstatus.dbid = flags.dbid) < 3"

    self.cur.execute(
      "SELECT DISTINCT flags.dbid FROM flags WHERE ghc=%(ghc)s {0} ORDER BY flags.dbid".format(filter_sql),
      {'ghc': self.ghc_id})

    return [c[0] for c in self.cur if not self.isMasked(c[0])]

  def getNumOfProblematicChannels(self, without_missing=False):
    return len(self.getProblematicChannels(without_missing))

  def getMissedChannels(self):
    self.classifyChannels()
    self.cur.execute("SELECT DISTINCT dbid FROM missed_channels WHERE ghc=%s ORDER BY dbid", (self.ghc_id,))
    return [c[0] for c in self.cur]

  def getNumOfActiveChannels(self, det, datatype=None):
    """
      Returns number of active channels (min for all gains)
    """
    return len(self.getActiveChannels(det=det, datatype=datatype))

  def getActiveChannels(self, datatype=None, det='ALL'):
    """
      Returns list of active channels (any of <datatype> flags)
    """
    if datatype is None:
      datatype = ['PED_OFF_MEAN%', 'PED_ON_MEAN%', 'ADC_MEAN%', 'APD_MEAN%']

    if is_iterable(datatype):
      sql_items = []
      values = {'ghc': self.ghc_id, 'det': det_to_sql(det)}
      for i, d in enumerate(datatype):
        sql_items.append("key LIKE %(datatype{0})s".format(i))
        values['datatype{0}'.format(i)] = d

      sql = "SELECT DISTINCT dbid FROM \"values\" INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) " \
            "WHERE ghc=%(ghc)s AND ({0}) AND dbid::text LIKE %(det)s".format(" OR ".join(sql_items))
      # logger.debug("getActiveChannels: %s", sql)
      self.cur.execute(sql, values)
    else:
      sql = self.cur.mogrify(
        "SELECT DISTINCT dbid FROM \"values\" INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) "
        "WHERE ghc=%(ghc)s AND key LIKE %(datatype)s AND dbid::text LIKE %(det)s",
        {'ghc': self.ghc_id, 'datatype': datatype, 'det': det_to_sql(det)})
      # logger.debug("getActiveChannels: %s", sql)
      self.cur.execute(sql)
    return [c[0] for c in self.cur if not self.isMasked(c[0])]

  def getDataKeys(self, datatype=None):
    """
      Returns available data keys.
    """
    if datatype is None:
      sql = "SELECT key FROM valuekeys"
      datatype = ""
    else:
      sql = "SELECT key FROM valuekeys WHERE keyid LIKE %s"
      datatype += '%'

    try:
      self.cur.execute(sql, (datatype,))
      return [c[0] for c in self.cur]
    except (IndexError, psycopg2.Error) as e:
      logger.exception("getDataKeys(%s) failed: %s", datatype, e)
      return []

  def resetFlags(self):
    """
      Reset flags in DB
    """
    self.cur.execute("DELETE FROM flags WHERE ghc=%s", (self.ghc_id,))
    self.cur.execute("DELETE FROM missed_channels WHERE ghc=%s", (self.ghc_id,))
    self.isClassified = False
    self.dbh.commit()

  def getChannelData(self, channel, key=None):
    """
      Returns channel's value for channels
      If additional keys ('key' and 'datatype') are specified -- return value
      else return dict with all values for channel
      :type key: None | list(str) | str
      :type channel: int | str
    """
    if not is_iterable(key):
      if self.isMasked(channel):
        return 0

    if key is None:
      key = self.getDataKeys()

    if not is_iterable(key):
      try:
        self.cur.execute(
          "SELECT value FROM values INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid)"
          "WHERE ghc = %(ghc)s AND dbid = %(ch)s AND key LIKE %(key)s",
          {'ghc': self.ghc_id, 'ch': channel, 'key': key + '%'})
        res = self.cur.fetchone()
        if res is None:
          # logger.debug("Value not found: ghc %s, dbid %s, key %s", self.ghc_id, channel, key)
          return None
        return res[0]
      except psycopg2.Error as e:
        # print "SQL error", str(e)
        logger.exception("getChannelData(%s, %s) failed: %s", channel, key, e)
        return None
    else:
      result = {}
      for k in key:  # TODO: is this used?
        # itertools.product(key):
        result[k] = self.getChannelData(k)

      return result

  def getPedestalFlags(self, channel):
    """
      Returns flags for pedestal channels
    """

    def PedestalComparison(gain, deadlimits, badlimits):
      tmpflags = []
      mean = self.getChannelData(channel, key='PED_ON_MEAN_' + gain)
      rms = self.getChannelData(channel, key='PED_ON_RMS_' + gain)
      if mean is None or rms is None:
        return []
      if mean <= deadlimits[0] or rms <= deadlimits[1]:
        tmpflags.append('DP' + gain)
      else:
        if badlimits[0] <= rms < badlimits[1] and mean > deadlimits[0]:
          tmpflags.append('LR' + gain)
        if rms > badlimits[1] and mean > deadlimits[0]:
          tmpflags.append('VLR' + gain)
        if abs(mean - 200) >= 30 and mean > deadlimits[0]:
          tmpflags.append('BP' + gain)
      return tmpflags

    flags = []
    if getSubDetector(channel) == 'EB':
      limits = {'G1': ((1, 0.2), (1.1, 3)), 'G6': ((1, 0.4), (1.3, 4)), 'G12': ((1, 0.5), (2.1, 6))}
    else:
      limits = {'G1': ((1, 0.2), (1.5, 4)), 'G6': ((1, 0.4), (2, 5)), 'G12': ((1, 0.5), (3.2, 7))}
    flags += PedestalComparison('G1', limits['G1'][0], limits['G1'][1])
    flags += PedestalComparison('G6', limits['G6'][0], limits['G6'][1])
    flags += PedestalComparison('G12', limits['G12'][0], limits['G12'][1])
    return list(set(flags))

  def classifyChannels(self):
    """
      Call getPedestalFlags for pedestals or execute sql quiery for compare test pulse,
      laser or pedestal HV OFF channels
    """
    if self.isClassified:
      # logger.debug("Already classified.")
      return

    logger.info("Performing channel classification")
    self.dbh.commit()

    def testpulse():
      for gain in ('G1', 'G6', 'G12'):
        sql = "INSERT INTO flags SELECT ghc, dbid, %s FROM \"values\" " \
              "INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) " \
              "WHERE ghc = %s AND key = %s AND value = 0"
        self.cur.execute(sql, ('DTP' + gain, self.ghc_id, 'ADC_MEAN_' + gain))
        for det in ('EE', 'EB'):
          l = det_to_sql(det)
          self.cur.execute("SELECT AVG(value) FROM \"values\" INNER JOIN valuekeys "
                           "ON (values.keyid = valuekeys.keyid) WHERE ghc = %s AND key = %s "
                           "AND dbid::text LIKE %s", (self.ghc_id, 'ADC_MEAN_' + gain, l))
          avg = self.cur.fetchone()[0]
          if avg is None:
            logger.info("No Testpulse data for gain %s and detector %s!", gain, det)
            continue

          sql = "INSERT INTO flags SELECT ghc, dbid, %s FROM \"values\" INNER JOIN valuekeys " \
                "ON (values.keyid = valuekeys.keyid) WHERE ghc = %s AND key = %s AND value::numeric > 0 " \
                "AND value::numeric <= 0.5 * {0} AND dbid::text LIKE %s".format(avg)
          self.cur.execute(sql, ('STP' + gain, self.ghc_id, 'ADC_MEAN_' + gain, l))

          sql = "INSERT INTO flags SELECT ghc, dbid, %s FROM \"values\" INNER JOIN valuekeys " \
                "ON (values.keyid = valuekeys.keyid) WHERE ghc = %s AND key = %s " \
                "AND value::numeric > 1.5 * {0} AND dbid::text LIKE %s".format(avg)
          self.cur.execute(sql, ('LTP' + gain, self.ghc_id, 'ADC_MEAN_' + gain, l))

    def ped_hvoff():
      # pedestal HV OFF channels problems only for EB
      cur_on = self.dbh.cursor()
      cur_off = self.dbh.cursor()
      pre = "^[BD]P"
      # Botjo checks only G12 RMS
      for gain in ["G12"]:
        data = defaultdict(lambda: [None, None])
        sql_on = "SELECT dbid, value FROM \"values\" INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) WHERE " \
                 "ghc=%s AND key='PED_ON_RMS_G12' AND dbid::text LIKE %s AND value::numeric > 0"
        cur_on.execute(sql_on, (self.ghc_id, '1%'))
        for dbid, value in cur_on:
          data[dbid][0] = float(value)

        sql_off = "SELECT dbid, value FROM \"values\" INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) WHERE " \
                  "ghc=%s AND key='PED_OFF_RMS_G12' AND dbid::text LIKE %s AND value::numeric > 0"
        cur_off.execute(sql_off, (self.ghc_id, '1%'))
        for dbid, value in cur_off:
          data[dbid][1] = float(value)

        badchannels = []
        for k, v in data.items():
          if v[0] is None or v[1] is None:
            logger.info("Missing pedestal data for channel %d: PED_ON_RMS_G12 = %s, PED_OFF_RMS_G12 = %s",
                        k, str(v[0]), str(v[1]))
            continue

          if abs(v[0] - v[1]) < 0.2:
            # logger.debug("Potential HV problem: channel %s", k)
            badchannels.append(k)

        for c in badchannels:
          # logger.debug("Checking channel %s: HV problem", c)
          self.cur.execute("SELECT flag FROM flags WHERE ghc = %s AND dbid = %s", (self.ghc_id, c))
          # logger.debug("- Flags: %s", ",".join(x[0] for x in self.cur))
          self.cur.execute("SELECT COUNT(dbid) FROM flags WHERE ghc = %s AND dbid = %s AND flag ~ %s",
                           (self.ghc_id, c, pre))
          ans = self.cur.fetchone()
          # logger.debug("- Number of pedestal flags: %s", ans[0])
          isgood = (ans[0] == 0)
          if isgood:
            # logger.debug("- Setting HV flag!")
            self.cur.execute("INSERT INTO flags VALUES (%s, %s, %s)", (self.ghc_id, c, 'BV' + gain))
            # else:
            #   logger.debug("- Not setting HV flag")

    def laser():
      self.cur.execute(
        "SELECT COUNT(DISTINCT(dbid)) FROM \"values\" INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) "
        "WHERE ghc = %s AND (key = %s OR key = %s)", (self.ghc_id, 'APD_MEAN', 'APD_RMS'))
      if self.cur.fetchone()[0] == 0:
        raise RuntimeError("No laser data found")

      sql = "INSERT INTO flags SELECT ghc, dbid, 'DLAMPL' FROM \"values\" INNER JOIN valuekeys " \
            "ON (values.keyid = valuekeys.keyid) WHERE key = 'APD_MEAN' AND value <= 0"
      self.cur.execute(sql)
      for l in ("1%", "2%"):
        sql = "SELECT AVG(value) FROM \"values\" INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) WHERE " \
              "ghc = %s AND key = 'APD_MEAN' AND value::numeric > 0 AND dbid::text LIKE %s"
        self.cur.execute(sql, (self.ghc_id, l))
        avg = self.cur.fetchone()[0]
        sql = "INSERT INTO flags SELECT ghc, dbid, 'SLAMPL' FROM \"values\" INNER JOIN valuekeys " \
              "ON (values.keyid = valuekeys.keyid) WHERE " \
              "ghc = %s AND key = 'APD_MEAN' AND value::numeric < {0} * 0.1 AND value::numeric > 0 " \
              "AND dbid::text like %s".format(avg)
        self.cur.execute(sql, (self.ghc_id, l))

        sql = "INSERT INTO flags SELECT dl1.ghc, dl1.dbid, 'LLERRO' FROM \"values\" AS dl1 " \
              "INNER JOIN \"values\" AS dl2 ON dl1.dbid = dl2.dbid AND d1.ghc = d2.ghc " \
              "WHERE dl1.keyid = (SELECT keyid FROM valuekeys WHERE key=%(key1)s) " \
              "AND dl2.keyid = (SELECT keyid FROM valuekeys WHERE key=%(key2)s) " \
              "AND d1.ghc = %(ghc)s " \
              "AND dl1.value::numeric > {0} * 0.1 AND dl2.value::numeric / dl1.value::numeric > 0.2".format(avg)
        self.cur.execute(sql, {'key1': 'APD_MEAN', 'key2': 'APD_RMS', 'ghc': self.ghc_id})

    logger.info("Classify Pedestal HV ON data ...")
    is_classified = True
    try:
      self.cur.execute("SELECT DISTINCT dbid FROM values WHERE ghc = %s AND keyid::text LIKE %s",
                       (self.ghc_id, '10__'))
      for c in [k[0] for k in self.cur]:
        for f in self.getPedestalFlags(c):
          self.cur.execute("INSERT INTO flags VALUES (%s, %s, %s)", (self.ghc_id, c, f))
      self.dbh.commit()
      logger.info("Finished.")
    except Exception as e:
      logger.info("Skipped: %s", e)
      logger.debug("Error details: ", exc_info=True)
      self.dbh.rollback()
      is_classified = False
    logger.info("Classify Test Pulse data ...")
    try:
      testpulse()
      self.dbh.commit()
      logger.info("Finished.")
    except Exception as e:
      logger.info("Skipped: %s", e)
      logger.debug("Error details: ", exc_info=True)
      self.dbh.rollback()
      is_classified = False
    logger.info("Classify Laser data ...")
    try:
      laser()
      self.dbh.commit()
      logger.info("Finished.")
    except RuntimeError as e:
      logger.info("Skipped: %s", e)
      self.dbh.rollback()
      is_classified = False
    except Exception as e:
      logger.info("Skipped: %s", e)
      logger.debug("Error details: ", exc_info=True)
      self.dbh.rollback()
      is_classified = False
    logger.info("Classify Pedestal HV OFF data ...")
    try:
      ped_hvoff()
      self.dbh.commit()
      logger.info("Finished.")
    except Exception as e:
      logger.info("Skipped: %s", e)
      logger.debug("Error details: ", exc_info=True)
      self.dbh.rollback()
      is_classified = False
    # missed channels
    logger.info("Try to find missed channels ...")
    # pedestal hv on/off and testpulse
    try:
      missed_channels = set()
      for t in ['pedestal_hvon', 'testpulse']:
        prefix = ("PED_ON", "ADC")[t == testpulse]
        for i, j in itertools.combinations(("G1", "G6", "G12"), 2):
          self.cur.execute("SELECT dbid FROM values "
                           "INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) "
                           "WHERE key = %(key)s AND ghc=%(ghc)s",
                           {'ghc': self.ghc_id, 'key': '{0}_RMS_{1}'.format(prefix, i)})

          set1 = set(itertools.chain.from_iterable(self.cur))
          self.cur.execute("SELECT dbid FROM values "
                           "INNER JOIN valuekeys ON (values.keyid = valuekeys.keyid) "
                           "WHERE key = %(key)s AND ghc=%(ghc)s",
                           {'ghc': self.ghc_id, 'key': '{0}_RMS_{1}'.format(prefix, j)})

          set2 = set(itertools.chain.from_iterable(self.cur))

          missed_channels = missed_channels | (set1 ^ set2)

      data = list(zip(itertools.repeat(self.ghc_id), missed_channels))
      logger.debug("Missing channels: %s", '; '.join('(%s, %s)' % x for x in data))
      self.cur.executemany("INSERT INTO missed_channels VALUES (%s, %s)", data)
      self.dbh.commit()
      logger.info("Finished")
    except Exception as e:
      logger.info("Skipped: %s", e)
      logger.debug("Error details: ", exc_info=True)
      self.dbh.rollback()
      is_classified = False
    if not is_classified:
      logger.info("NOT ALL SELECTION CRITERIA ARE USED FOR DATA CLASSIFICATION")
    self.isClassified = True
    self.dbh.commit()

  def getFlagsForChannel(self, channel):
    if self.isMasked(channel):
      return []

    self.classifyChannels()
    self.cur.execute("SELECT flag FROM flags WHERE ghc = %s AND dbid = %s", (self.ghc_id, int(channel)))
    return [f[0] for f in self.cur]

  def getChannelsWithFlag(self, flags, exp="and", det=None):
    """
      Returns list of channels which has <flags> (string|list)
      exp = 'or' | 'and'
      note: inexact match possible (like)
    """
    self.classifyChannels()
    values = {'ghc': self.ghc_id}
    if exp == 'and':
      verb = ' INTERSECT '
    else:
      verb = ' UNION '

    if det:
      sql_det = " AND dbid::text LIKE %(det)s"  # .format(det_to_sql(det))
      values['det'] = det_to_sql(det)
    else:
      sql_det = ""

    if is_iterable(flags):
      sql = "SELECT DISTINCT dbid FROM (" + \
            verb.join("(SELECT dbid FROM flags WHERE ghc=%(ghc)s AND flag LIKE %(flag{0})s{1})".format(i, sql_det)
                      for i in range(len(flags))) + ') AS derivedTable'
      values.update(dict(('flag' + str(i), flags[i]) for i in range(len(flags))))
    else:
      sql = "SELECT DISTINCT dbid FROM flags WHERE flag LIKE %(flag)s AND ghc = %(ghc)s" + sql_det
      values['flag'] = flags

    logger.debug('SQL: %s', self.cur.mogrify(sql, values))

    self.cur.execute(sql, values)
    return [c[0] for c in self.cur if not self.isMasked(c[0])]

  def getNumChannelsWithFlag(self, flags, exp="and", det=None):
    """
      Returns list of channels which has <flags> (string|list)
      exp = 'or' | 'and'
      note: inexact match possible (like)
    """
    return len(self.getChannelsWithFlag(flags, exp, det))

  def readData(self, source, runs, data_type, lasertable=""):
    """
      Read pedestal values from database
        source    : connection string to database
        runs       : array of runs which contains data
        data_type       : run type
        lasertable : table of laser's data
    """
    if "oracle" not in source:
      self.readDataFromFile(data_type, files=runs)
      return
    if lasertable:
      logger.info("Table {0} will be user as source for Laser data".format(lasertable))
    # else:
    if len(runs) == 1:
      runs = "G12:{0} G6:{0} G1:{0}".format(runs[0]).split()

    logger.info("Trying to connect to Oracle")
    if pfgutils.connection.oradbh is None:
      logger.error("Requested source (Oracle) is not available!")
      return

    logger.info("OK")
    logger.info("Exporting data from Oracle to local DB ...")

    for gain_run in runs:
      if 'laser' not in data_type:
        gain = gain_run.split(':')[0]
        run = gain_run.split(':')[1]
        logger.info("Process {2} run {0} ({1}) ...".format(run, gain, data_type))
      else:
        run = gain_run
        gain = ""
        logger.info("Process {1} run {0} ...".format(run, data_type))

      cur = pfgutils.connection.oradbh.cursor()
      res = cur.execute(
        "SELECT IOV_ID from MON_RUN_IOV where RUN_IOV_ID=(select IOV_ID from RUN_IOV where RUN_NUM=:1)",
        (run,)).fetchone()
      if res:
        iov = res[0]
      else:
        logger.error("IOV not found for run {0}".format(run))
        cur.close()
        return

      if "pedestal" in data_type:
        sql = "select LOGIC_ID, PED_MEAN_{0}, PED_RMS_{0} from MON_PEDESTALS_DAT where IOV_ID=:1".format(gain)
        if data_type == "pedestal_hvon":
          fields = [x + gain for x in ['PED_ON_MEAN_', 'PED_ON_RMS_']]
        else:
          fields = [x + gain for x in ['PED_OFF_MEAN_', 'PED_OFF_RMS_']]
      elif "testpulse" in data_type:
        sql = "select LOGIC_ID, ADC_MEAN_{0}, ADC_RMS_{0} from MON_TEST_PULSE_DAT where IOV_ID=:1".format(gain)
        fields = [x + gain for x in ['ADC_MEAN_', 'ADC_RMS_']]
      elif "laser" in data_type:
        # TODO: check keys in DB
        sql = "select LOGIC_ID, APD_MEAN, APD_RMS, APD_OVER_PN_MEAN, APD_OVER_PN_RMS from {0} where IOV_ID=:1".format(lasertable)
        fields = ['APD_MEAN', 'APD_RMS', 'APD_OVER_PN_MEAN', 'APD_OVER_PN_RMS']
      else:
        logger.error("Unknown table: {0}".format(data_type))
        cur.close()
        return

      cur.close()
      cur = self.dbh.cursor()
      result = pfgutils.connection.oradbh.cursor().execute(sql, (iov,))
      cur.execute("INSERT INTO runs VALUES (%s, %s, %s, %s)", (self.ghc_id, run, data_type, gain))
      counter = 0
      for row in result:
        for k in range(len(fields)):
          cur.execute("INSERT INTO \"values\" VALUES (%(ghc)s, %(dbid)s"
                      ", (SELECT keyid FROM valuekeys WHERE key=%(key)s), %(value)s)",
                      {'ghc': self.ghc_id, 'dbid': row[0], 'key': fields[k], 'value': row[k + 1]})
        counter += 1
      logger.info("Exported {0} records".format(counter))
      self.dbh.commit()

  def readDataFromFile(self, datatype, files):
    """
      Read data from file called 'source'
    """
    if "pedestal_hvon" in datatype:
      fields = ['PED_ON_MEAN_G1', 'PED_ON_RMS_G1', 'PED_ON_MEAN_G6', 'PED_ON_RMS_G6',
                'PED_ON_MEAN_G12', 'PED_ON_RMS_G12']
    elif "pedestal_hvoff" in datatype:
      fields = ['PED_OFF_MEAN_G1', 'PED_OFF_RMS_G1', 'PED_OFF_MEAN_G6', 'PED_OFF_RMS_G6',
                'PED_OFF_MEAN_G12', 'PED_OFF_RMS_G12']
    elif "testpulse" in datatype:
      fields = ['ADC_MEAN_G1', 'ADC_MEAN_G6', 'ADC_MEAN_G12', 'ADC_RMS_G1', 'ADC_RMS_G6', 'ADC_RMS_G12']
    elif "laser" in datatype:
      fields = ['APD_MEAN', 'APD_RMS', 'APD_OVER_PN_MEAN', 'APD_OVER_PN_RMS']
    else:
      logger.error("Unsuported type of data: {0}".format(datatype))
      return

    seen_channels = []

    for f in files:
      logger.info("Reading file '{0}'".format(f))
      fh = open(f, 'r')
      cur = self.dbh.cursor()
      for line in fh.readlines():
        line = line.strip().split()
        channel = line[1]
        if channel in seen_channels:
          logger.warning("Duplicate channel %s", channel)
          continue
        seen_channels.append(channel)
        for k in range(len(fields)):
          cur.execute(
            "INSERT INTO \"values\" VALUES (%(ghc)s, %(dbid)s"
            ", (SELECT keyid FROM valuekeys WHERE key=%(key)s), %(value)s)",
            {'ghc': self.ghc_id, 'dbid': channel, 'key': fields[k], 'value': line[k + 2]})
      fh.close()
      cur.close()
    self.dbh.commit()

  def printProblematicChannelsCSV(self, output=None):
    """
      Print problematic channel's data
    """
    ostream = output or sys.stdout
    print(" {0:^10s} | {2:^30s} | {1:^40s}".format("channel", "coordinates", "flags"), file=ostream)
    if output is None:
      print("-" * 80, file=ostream)

    for chid in self.getProblematicChannels():
      flags = self.getFlagsForChannel(chid)
      # info = getChannelInfo(chid)
      if getSubDetector(chid) == 'EE':
        data = list(getXYZ(chid))
        data.extend([getDetSM(chid), getTT(chid)])
        coord = "iX={0:+3d} iY={1:+3d} iZ={2:+1d} {3:5s} TT{4:2d}".format(*data)
      else:
        data = list(getEtaPhi(chid))
        data.extend([getDetSM(chid), getTT(chid)])
        coord = "iEta={0:+2d} iPhi={1:3d} {2:5s} TT{3:2d}".format(*data)

      print(" {0:10d} | {2:30s} | {1:40s} ".format(chid, "+".join(flags), coord), file=ostream)
    if output is None:
      print("-" * 80, file=ostream)

  def printProblematicChannelsTable(self, output=None):
    """
      Print problematic channel's data
    """
    ostream = output or sys.stdout
    print("|_. {0:^10s} |_\\2. {2:^30s} |_. {1:^40s} |".format("Channel ID", "Flags", "Info"), file=ostream)
    for chid in self.getProblematicChannels():
      flags = self.getFlagsForChannel(chid)
      if getSubDetector(chid) == 'EE':
        data = list(getXYZ(chid))
        data.extend([getDetSM(chid), getTT(chid)])
        coord = "iX={0:+3d} iY={1:+3d} iZ={2:+1d} | {3:5s} TT{4:2d}".format(*data)
      else:
        data = list(getEtaPhi(chid))
        data.extend([getDetSM(chid), getTT(chid)])
        coord = "iEta={0:+2d} iPhi={1:3d} | {2:5s} TT{3:2d}".format(*data)

      print("| {0:10d} | {2:30s} | {1:40s} |".format(chid, "+".join(flags), coord), file=ostream)

  # def getchnum(self, d, x):
  #   assert not isinstance(x, basestring)
  #   if len(x) != 0:
  #     exsql = 'AND dbid IN ' + " AND dbid IN ".join(
  #       ["(SELECT dbid FROM flags WHERE flag ~ '{0}' AND ghc = {1})".format(i, self.ghc_id) for i in x])
  #   else:
  #     exsql = ''
  #
  #   # at least philosophy
  #   sql = "SELECT COUNT(DISTINCT dbid) FROM flags WHERE ghc = {ghc} AND dbid::text LIKE '{loc}' {exsql} " \
  #         "AND NOT dbid IN (SELECT dbid FROM missed_channels WHERE ghc={ghc})"
  #   sql = sql.format(ghc=self.ghc_id, loc=det_to_sql(d), exsql=exsql)
  #   # logger.debug('GetChNum SQL %s', sql)
  #
  #   self.cur.execute(sql)
  #   row = self.cur.fetchone()
  #   return row[0] if row else 0

  @property
  def has_laser(self):
    if self._has_laser is None:
      self._has_laser = (self.getNumOfActiveChannels(det='ALL', datatype='APD_MEAN%') > 0)

    return self._has_laser

  @property
  def has_testpulse(self):
    if self._has_testpulse is None:
      self._has_testpulse = (self.getNumOfActiveChannels(det='ALL', datatype='ADC_MEAN%') > 0)

    return self._has_testpulse

  @property
  def has_ped_hvon(self):
    if self._has_ped_hvon is None:
      self._has_ped_hvon = self.getNumOfActiveChannels(det='ALL', datatype='PED_ON_MEAN%') > 0

    return self._has_ped_hvon

  @property
  def has_ped_hvoff(self):
    if self._has_ped_hvoff is None:
      self._has_ped_hvoff = self.getNumOfActiveChannels(det='ALL', datatype='PED_OFF_MEAN%') > 0

    return self._has_ped_hvoff

  def get_runs(self):
    if self.isClassified:
      self.cur.execute("SELECT run, type, comment FROM runs WHERE ghc=%s", (self.ghc_id,))
      res = {}
      for run, run_type, comment in self.cur:
        if run_type not in res:
          res[run_type] = {}

        res[run_type][comment] = run

      return res

  def have_datatype(self, datatype):
    if datatype is not None:
      if any(datatype.startswith(x) for x in self.PEDESTAL_FLAGS) and not self.has_ped_hvon:
        return False

      if any(datatype.startswith(x) for x in self.HV_FLAGS) and not self.has_ped_hvoff:
        return False

      if any(datatype.startswith(x) for x in self.TESTPULSE_FLAGS) and not self.has_testpulse:
        return False

      if any(datatype.startswith(x) for x in self.LASER_FLAGS) and not self.has_laser:
        return False

    return True


def getChannelInfo(c):
  """
    Return dict with information about location of channels in ECAL
    keys for EB: id, location, SM, TT, iEta, iPhi
    keys for EE: id, location, SM, Dee, iX, iY, iZ
  """
  info = {'id': c}
  info.update(pfgutils.connection.getChDict(c))
  return info


# def getChDict(channel):
#   # cur_chdb.execute("SELECT * FROM channels WHERE dbId = %s", (channel,))
#   # cur_chdb.execute("SELECT * FROM channels WHERE dbId = ?", (channel,))
#   # return cur_chdb.fetchone()
#   return pfgutils.connection.getChDict(channel=)


def getTT(channel):
  """
    Returns TT number for channel
  """
  return pfgutils.connection.getChDict(channel)['tower']


def getCCU(channel):
  return pfgutils.connection.getChDict(channel)['ccu']


def getXtal(channel):
  """
    Returns crystal number for channel
  """
  return pfgutils.connection.getChDict(channel)['xtalinccu']


def getDetSM(channel):
  return pfgutils.connection.getChDict(channel)['det']


def getSM(channel):
  """
    Returns SM number for EB channel
  """
  return pfgutils.connection.getChDict(channel)['det'][2:]


def getEtaPhi(channel):
  """
    Return (Eta, Phi) tuple for EB channels
  """
  r = pfgutils.connection.getChDict(channel)
  return r['ieta'], r['iphi']


def getEtaPhiBin(channel):
  """
    Return (Eta, Phi) tuple for EB channels
  """
  r = pfgutils.connection.getChDict(channel)
  return r['ieta'] + 86, r['iphi']


def getXYZ(channel):
  """
    Return (x, y , -1|1 ) tuple for EE channels
  """
  r = pfgutils.connection.getChDict(channel)
  return r['ix'], r['iy'], r['iz']


def getSubDetector(channel):
  """
    Returns EB|EE detector place of channel
  """
  return pfgutils.connection.getChDict(channel)['det'][:2]


def det_to_sql(det):
  """
  Returns SQL condition for selecting channels in a given subdetector

  :type det: str
  :param det: subdetector (EE, EB, ALL)
  :rtype: str
  """
  if det.endswith('%'):
    logger.warning('det_to_sql called with argument already in SQL format!')
    logger.debug(inspect.stack()[1][3])
    return det
  return '2%' if det == 'EE' else ('1%' if det == 'EB' else '%')


def is_iterable(thing):
  return isinstance(thing, Iterable) and not isinstance(thing, str)
