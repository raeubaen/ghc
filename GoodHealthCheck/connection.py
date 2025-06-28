#!/usr/bin/env python

import sys

import os
import sqlite3
import logging
import Settings
from pfgutils.dqm.DQMURLProvider import DQMURLProvider
import pickle
import pandas as pd
import traceback

dqms = {'online': DQMURLProvider("online"), "offline": DQMURLProvider("offline")}

ecalchannels_path = os.path.dirname(os.path.realpath(__file__))+"/ecalchannels.csv"
pickle_file =  os.path.dirname(__file__)+"/ch_dict.pkl"


try:
  import cx_Oracle
except ImportError:
  logging.warning("Oracle module not available!")
  cx_Oracle = None
  oradbh = None

class Connection:

    _instance = None
    _oradbh = None
    _ecalchannels = None

    def __new__(cls):
        """Singleton connection class creation"""
        if cls._instance is None:
            cls._instance = super(Connection, cls).__new__(cls)    

            if cx_Oracle:    
                try:
                    """:type: cx_Oracle.Connection"""
                    dsn = cx_Oracle.makedsn("127.0.0.1", 10121, service_name=Settings.Oracle['SID'])
                    cls._instance._oradbh = cx_Oracle.connect(user=Settings.Oracle['user'], password=Settings.Oracle['password'], dsn=dsn, encoding="UTF-8")
                    print("ORACLE CONNECTED")
                except Exception:
                    logging.warning("Cannot connect to Oracle database")
                    cls._instance._oradbh = None
                    print(traceback.format_exc())

                try:
                    """:type: ecalchannels.Connection """
                    if not os.path.exists(pickle_file):
                        df  = pd.read_csv(ecalchannels_path)
                        df.columns = df.columns.map(str)
                        dbid_col = df.columns[17]
                        df.set_index(dbid_col, inplace=True)
                        cls._instance._ecalchannels = df.to_dict(orient='index')
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(cls._instance._ecalchannels, f)
                    else:
                        with open(pickle_file, 'rb') as f:
                            cls._instance._ecalchannels = pickle.load(f)
                    print("ECAL CHANNELS CONNECTED")
                except Exception:
                    logging.warning("Cannot connect to EcalChannels CSV")
                    cls._instance._ecalchannels = None
                    print(traceback.format_exc())
                    sys.exit(-1)
        return cls._instance

    def getChDict(self, c):
        return self._ecalchannels.get(c, None)

