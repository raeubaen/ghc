#!/usr/bin/env python

import os
import sqlite3
import logging
from . import Settings
from pfgutils.dqm.DQMURLProvider import DQMURLProvider
import pickle
import pandas as pd

dqms = {'online': DQMURLProvider("online"), "offline": DQMURLProvider("offline")}

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
    dsn = cx_Oracle.makedsn("127.0.0.1", 10121, service_name=Settings.Oracle['SID'])
    oradbh = cx_Oracle.connect(user=Settings.Oracle['user'], password=Settings.Oracle['password'], dsn=dsn, encoding="UTF-8")
    print("ORACLE CONNECTED")
  except:
    logging.warning("Cannot connect to Oracle database")
    oradbh = None


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

ecalchannels_path = '/afs/cern.ch/user/c/charlesf/ghc/GoodHealthCheck/ecalchannels.csv'
ecalch_df = pd.read_csv(ecalchannels_path, header=None)

pickle_file = '/afs/cern.ch/user/c/charlesf/ghc/pfgutils/pfgutils/ch_dict.pkl'
channel_dict = None

def loadChDict():   
    global channel_dict

    if channel_dict is not None:
        return channel_dict

    if not os.path.exists(pickle_file):
        ecalchannels_path = '/afs/cern.ch/user/c/charlesf/ghc/GoodHealthCheck/ecalchannels.csv'
        df = pd.read_csv(ecalchannels_path, header=0)
        df.columns = df.columns.map(str)
        dbid_col = df.columns[17]
        df.set_index(dbid_col, inplace=True)
        channel_dict = df.to_dict(orient='index')

        with open(pickle_file, 'wb') as f:
            pickle.dump(channel_dict, f)
    else:
        with open(pickle_file, 'rb') as f:
            channel_dict = pickle.load(f)
    

    return channel_dict

def getChDict(c):
    ch_dict = loadChDict()
    return ch_dict.get(c, None)

#ecalchannels = sqlite3.connect(os.path.join(os.path.dirname(__file__), "ecalchannels.db"))
#ecalchannels.row_factory = dict_factory
#
#try:
#  import psycopg2
#  from psycopg2.extras import DictCursor
#except ImportError:
#  logging.warning("psycopg2 module is not available!")
#  psycopg2 = None
#  ecalchannelstatus = None
#else:
#  # ecalchannelstatus connection
#  try:
#    ecalchannelstatus = psycopg2.connect(
#    "host='{host}' dbname='ecalchannelstatus' user='{user}' password='{password}'".format(
#      host=Settings.Database['options']['host'], user=Settings.Database['options']['user'],
#      password=Settings.Database['options']['password'], ))
#  except:
#    logging.warning("Cannchannel_dict = {ot connect to ecalchannelstatus database")
#    ecalchannelstatus = None
