#!/usr/bin/env python



import hashlib
import json
import os.path
import warnings
import sys

with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  import requests

from pfgutils.Settings import certpath, keypath, cacert

_cache = {}


def loadCache(cachedir="/tmp"):
  import sqlite3
  global _cache
  if not os.path.exists(os.path.join(cachedir, "pfgutils.dqm.json.cache.db")):
    return
  db = sqlite3.connect(os.path.join(cachedir, "pfgutils.dqm.json.cache.db"))
  cur = db.cursor()
  for row in cur.execute("select * from data"):
    _cache[row[0]] = json.loads(row[1])
  db.close()


def dumpCache(cachedir="/tmp"):
  import sqlite3
  global _cache
  if not os.path.exists(cachedir):
    os.makedirs(cachedir)
  if os.path.exists(os.path.join(cachedir, "pfgutils.dqm.json.cache.db")):
    os.remove(os.path.join(cachedir, "pfgutils.dqm.json.cache.db"))
  db = sqlite3.connect(os.path.join(cachedir, "pfgutils.dqm.json.cache.db"))
  cur = db.cursor()
  cur.execute("create table data(url text primary key not null, json text)")
  for key in _cache:
    cur.execute("insert into data values (?, ?)", (key, json.dumps(_cache[key])))
  db.commit()
  db.close()


def get(run, histogrampath, dataset="Global/Online/ALL"):
  url = getJSONURL(run, histogrampath, dataset)
  if url is not None:
    return requestJSON(url)
  return None


def requestJSON(url, method="GET"):
  import re
  if url in _cache:
    return _cache[url]
  r = requests.request(method, url, cert=(certpath, keypath), verify=cacert)
  r.raise_for_status()
  jsonstr = r.text
  jsonstr = re.sub(",(|-)?inf,", ",\"\\1inf\",", jsonstr)  # ,-inf, --> ,"-inf",
  j = verifyJSON(jsonstr)
  if j is not None:
    _cache[url] = j
  return j


def verifyJSON(jsonstr):
  try:
    s = json.loads(jsonstr)
  except ValueError:
    return None
  if "hist" not in s or s["hist"] == "unsupported type":
    return None
  return s


def getJSONURL(run, histogrampath, dataset="online"):
  if dataset == "online":
    dataset = "Global/Online/ALL"
  while "Run summary" in histogrampath:
    histogrampath = "/".join(histogrampath.split("/")[1:])
  histogrampath = histogrampath.lstrip('/')
  dataset = dataset.lstrip('/')
  if dataset == "Global/Online/ALL":
    dqmtype = "online"
  elif dataset != "":
    dqmtype = "offline"
  else:
    return None
  return os.path.join("https://cmsweb.cern.ch/dqm/{0}/jsonfairy/archive/{1}/".format(dqmtype, run), dataset,
                      histogrampath)


def JSON2ROOT(data):
  if data is None:
    return None
  import ROOT
  data = data['hist']
  if data == "unsupported type":
    return None
  title = data['title']
  name = data['stats']['name']
  # axis: (title, min, max, bins)
  titles = {}
  axisdict = {}
  for axis in ('yaxis', 'xaxis'):
    if axis not in data:
      data[axis] = {}
    titles[axis] = "" if 'title' not in data[axis] else data[axis]['title']
    atitle = "" if axis not in titles else titles[axis]
    afirstvalue = 0 if 'first' not in data[axis] or 'value' not in data[axis]['first'] else data[axis]['first']['value']
    alastvalue = 1 if 'last' not in data[axis] or 'value' not in data[axis]['last'] else data[axis]['last']['value']
    try:
      anbins = data[axis]['last']['id'] - data[axis]['first']['id'] + 1
    except:
      anbins = 1
    axisdict[axis] = (atitle, afirstvalue, alastvalue, anbins)
  xaxis = axisdict['xaxis']
  yaxis = axisdict['yaxis']
  if "2" in data['type']:
    thtype = "TH2"
    h = ROOT.TH2D(name, title, xaxis[3], xaxis[1], xaxis[2], yaxis[3], yaxis[1], yaxis[2])
    h.GetYaxis().SetTitle(yaxis[0])
  else:
    thtype = "TH1"
    h = ROOT.TH1D(name, title, xaxis[3], xaxis[1], xaxis[2])
  h.GetXaxis().SetTitle(xaxis[0])
  content = data['bins']['content']
  if thtype == "TH1":
    content = [content]
  for ybin in range(len(content)):
    row = content[ybin]
    for xbin in range(len(row)):
      item = row[xbin]
      if item == 'inf':
         item = sys.float_info.max
      elif item == '-inf':
         item = -sys.float_info.max
      #      print "set", item, "to", xbin, ybin
      if thtype == "TH2":
        h.SetBinContent(xbin + 1, ybin + 1, item)
      else:
        h.SetBinContent(xbin + 1, item)
  if 'yaxis' in data and 'labels' in data['yaxis']:
    for ybin, label in [(data['yaxis']['labels'].index(x), x['value']) for x in data['yaxis']['labels']]:
      h.GetYaxis().SetBinLabel(ybin + 1, label)
  if 'xaxis' in data and 'labels' in data['xaxis']:
    for xbin, label in [(data['xaxis']['labels'].index(x), x['value']) for x in data['xaxis']['labels']]:
      h.GetXaxis().SetBinLabel(xbin + 1, label)
  h.SetMaximum(data['values']['max'])
  h.SetMinimum(data['values']['min'])
  h.ResetStats()
  ROOT.SetOwnership(h, False)
  return h
