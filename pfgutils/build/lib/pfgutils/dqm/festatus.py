#!/usr/bin/env python

from pfgutils.dqm.json import get


def getFEStatus(run, det, sm, dataset="online"):
  """
  FE Status for SM
  :param run: int
  :param det: str
  :param sm: int
  :param dataset: str
  :return: dict
  """
  det = det.upper()
  if det != 'EB' and det != 'EE':
    raise RuntimeError("det should be in ['ee', 'eb', 'EE', 'EB']")
  status = get(run, "Ecal{1}/{0}StatusFlagsTask/FEStatus/{0}SFT front-end status bits {0}{2:+03d}".format(det,
    ("Endcap", "Barrel")[det == 'EB'], sm), dataset)
  if status is None:
    RuntimeWarning("FE status hist is empty")
    return {}
  data = status['hist']['bins']['content']
  res = {}
  labels = status['hist']['yaxis']['labels']
  for err in labels:
    ybin = labels.index(err)
    res[err['value']] = {}
    for pos in range(len(data[ybin])):
      res[err['value']][pos + 1] = data[ybin][pos]
  return res


def getNumOfBadTT(run, det, sm, dataset='online'):
  data = getFEStatus(run, det, sm, dataset)
  res = {}
  for key in data:
    res[key] = len([x for x in data[key] if data[key][x] != 0])
  return res


def getSummaryFEStatus(run, det, sm, dataset='online', percent=False):
  """
  FE Status summary for SM
  :param run: int
  :param det: str
  :param sm: int
  :param dataset: str
  :return: dict
  """
  det = det.upper()
  data = getFEStatus(run, det, sm, dataset)
  summary = {}
  for errkey in data:
    summary[errkey] = 0
    summary[errkey] += sum([data[errkey][x] for x in data[errkey]])
  if percent:
    summ = sum([summary[x] for x in summary])
    for errkey in summary:
      summary[errkey] = float(summary[errkey]) / summ
  return summary


def getSummaryStatus(run, det, dataset='online', percent=False):
  det = det.upper()
  summary = {}
  maxfe = [x[1] for x in zip(["EE", "EB"], (9, 18)) if x[0] == det][0]
  for sm in range(-maxfe, maxfe + 1):
    if sm == 0:
      continue
    psumm = getSummaryFEStatus(run, det, sm, dataset)
    if len(list(summary.keys())) == 0:
      list(map(lambda x: summary.update({x: 0}), psumm))
    for key in psumm:
      summary[key] += psumm[key]
  if percent:
    summ = sum([summary[x] for x in summary])
    for key in summary:
      summary[key] = float(summary[key]) / summ
  return summary
