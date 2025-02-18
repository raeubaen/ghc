#!/usr/bin/env python

# import sys
# import urllib2
# import httplib
import re
import os
import warnings
import logging

with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  import requests

from pfgutils.Settings import certpath, keypath, cacert


def getDatasetFromFilename(filename):
  filename = os.path.basename(filename)
  parts = filename.split('__')[1:]
  parts[-1] = parts[-1].replace('.root', '')
  parts = [''] + parts
  return '/'.join(parts)


# noinspection PyMethodMayBeStatic
class DQMURLProvider(object):
  hrefre = re.compile(".*<a href=(.+)>.*</a>.*")

  def __init__(self, dqmtype="online"):
    if dqmtype == "offline":
      self.DQMURL = "https://cmsweb.cern.ch/dqm/offline/data/browse/ROOT/OfflineData"
    elif dqmtype == "online":
      self.DQMURL = "https://cmsweb.cern.ch/dqm/online/data/browse/Original"
    else:
      raise RuntimeError("Unsupported DQM type")

    self._dqmtype = dqmtype
    self._cache = {'datasets': set(), 'urls': {}, 'urlcheck': {}}

  def getDQMType(self):
    return self._dqmtype

  def requestHTML(self, url, method='GET'):
    r = requests.request(method, url, cert=(certpath, keypath), verify=cacert)
    r.raise_for_status()
    return r.text

  def checkURL(self, url):
    if url in self._cache['urlcheck']:
      return self._cache['urlcheck'][url]
    f = requests.get(url, cert=(certpath, keypath), verify=cacert)
    r = True if f.status_code == 200 else False
    self._cache['urlcheck'][url] = r
    return r

  def _getURL(self, url, includedirs=False, includefiles=True, recursive=True):
    res = []
    if url in self._cache['urls']:
      a = self._cache['urls'][url]
    else:
      f = self.requestHTML(url)
      x = [x.strip() for x in f.split("<tr>")]
      a = []
      for l in x:
        if "Up" in l:
          continue
        a.extend(self.hrefre.findall(l))
      a = [x.strip("'") for x in a]
      a = ["https://cmsweb.cern.ch" + x for x in a]
    for x in a:
      if includefiles and ".root" in x:
        res.append(x)
      if includedirs and ".root" not in x:
        res.append(x)
      if recursive and ".root" not in x:
        res.extend(self._getURL(x))
    if url not in self._cache['urls']:
      self._cache['urls'][url] = res
    return res

  def _getSubDirs(self, url):
    return [os.path.basename(x.rstrip("/")) for x in self._getURL(url, includedirs=True, includefiles=False, recursive=False)]

  def _getRunFiles(self, datadir, run):
    d = [x for x in self._getSubDirs(os.path.join(self.DQMURL, datadir)) if re.match(x.replace("x", ".*"), "000" + str(run))]
    if len(d) != 0:
      d = d[0]
    else:
      # no such root file in given url
      return []
    files = [x for x in self._getURL(os.path.join(self.DQMURL, datadir, d)) if str(run) in x]
    return files

  def _getDatadirsFromDQMDataset(self, dataset):
    if dataset == 'online':
      return self.getDatadirs()
    reversedds = ["/".join(reversed(x.split("/"))) for x in self.getDatadirs()]
    if dataset.startswith('/'):
      dataset = dataset[1:]
    if len(dataset.split('/')) == 1:
      raise RuntimeError("Too less / in dataset")
    matchstr = os.path.join(dataset.strip().split('/')[0], dataset.strip().split('/')[1].split('-')[0])
    matchstrre = re.compile(matchstr)
    reversedds = [x for x in reversedds if matchstrre.match(x)]
    return ["/".join(reversed(x.split("/"))) for x in reversedds]

  @staticmethod
  def _getDatasetFilePart(dataset):
    return dataset.strip().replace("/", "__")

  def getFilesInDataset(self, run, dataset):
    datadirs = self._getDatadirsFromDQMDataset(dataset)
    if len(datadirs) == 0:
      logging.warning("No datasets found")
      return []
    tmp = []
    for datadir in datadirs:
      datapattern = self._getDatasetFilePart(dataset)
      datapatternre = re.compile(datapattern)
      tmp += [x for x in self._getRunFiles(datadir, run) if len(datapatternre.findall(x)) != 0]
    f = getDatasetFromFilename if dataset != 'online' else lambda x: 'online'
    return [(f(x), x) for x in tmp]

  def getDatadirs(self):
    if self._dqmtype == "online":
      return self._getSubDirs(self.DQMURL)
    if len(self._cache['datasets']) == 0:
      for d1 in self._getSubDirs(self.DQMURL):
        for d2 in self._getSubDirs(os.path.join(self.DQMURL, d1)):
          self._cache['datasets'].add(os.path.join(d1, d2))
    return self._cache['datasets']

  def getAllRunFiles(self, run):
    res = set()
    sds = self.getDatadirs()
    if self._dqmtype == "online":
      sds = [x for x in sds if re.match(x.replace("x", ".*"), "000" + str(run))]
    idx = 1
    for dataset in sds:
      res = res.union(set(self._getRunFiles(dataset, run)))
      idx += 1
    return res
