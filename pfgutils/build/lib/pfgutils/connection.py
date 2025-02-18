#!/usr/bin/env python

import os
import sqlite3
import logging
from . import Settings
from pfgutils.dqm.DQMURLProvider import DQMURLProvider


dqms = {'online': DQMURLProvider("online"), "offline": DQMURLProvider("offline")}

def connect(oracle=True, chanstat=True):
  try:
    import cx_Oracle
  except ImportError:
    logging.warning("Oracle module not available!")
    cx_Oracle = None
    oradbh = None
  else:
    #os.environ['TNS_ADMIN'] = os.path.dirname(os.path.abspath(__file__))
    """:type: cx_Oracle.Connection"""
    try:
      oradbh = cx_Oracle.connect(
        "{0}/{1}@{2}".format(Settings.Oracle['user'], Settings.Oracle['password'], Settings.Oracle['SID']))
    except:
      logging.warning("Cannot connect to Oracle database")
      oradbh = None


  def dict_factory(cursor, row):
      d = {}
      for idx, col in enumerate(cursor.description):
          d[col[0]] = row[idx]
      return d

  ecalchannels = sqlite3.connect(os.path.join(os.path.dirname(__file__), "ecalchannels.db"))
  ecalchannels.row_factory = dict_factory

  try:
    import psycopg2
    from psycopg2.extras import DictCursor
  except ImportError:
    logging.warning("psycopg2 module is not available!")
    psycopg2 = None
    ecalchannelstatus = None
  else:
    # ecalchannelstatus connection
    try:
      ecalchannelstatus = psycopg2.connect(
      "host='{host}' dbname='ecalchannelstatus' user='{user}' password='{password}'".format(
        host=Settings.Database['options']['host'], user=Settings.Database['options']['user'],
        password=Settings.Database['options']['password'], ))
    except:
      logging.warning("Cannot connect to ecalchannelstatus database")
      ecalchannelstatus = None
