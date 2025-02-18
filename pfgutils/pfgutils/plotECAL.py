#!/usr/bin/env python

import ROOT
import logging
from itertools import repeat

ROOT.gROOT.SetBatch(ROOT.kTRUE)

_EB_text = []
_EE_lines = []
_EE_text = []


def _drawEBextra(parent, number):
  p = parent.cd(number)
  global _EB_text

  def drawEBNumbers():
    l = ROOT.TLatex()
    _EB_text.append(l)
    l.SetTextSize(0.03)
    for y in ((42.5, "+"), (-42.5, "-")):
      idx = 1
      for x in range(5, 360, 20):
        l.DrawLatex(x, y[0], "{0}{1:2d}".format(y[1], idx))
        idx += 1
    ROOT.gStyle.SetOptStat("e")
    ROOT.gStyle.SetTickLength(0.01, "xy")

  drawEBNumbers()


def _drawEEextra(parent, number, z=1):
  p = parent.cd(number)
  global _EE_lines
  global _EE_text

  def DrawLine(x, y):
    line = ROOT.TPolyLine()
    for pline in range(len(x)):
      line.SetNextPoint(x[pline], y[pline])
      line.SetLineColor(1)
      line.SetLineWidth(2)
    return line

  def getEENumbers():
    l = ROOT.TLatex()
    _EE_text.append(l)
    l.SetTextSize(0.04)
    # Dee 
    if z == 1:
      l.DrawLatex(5, 95, "Dee1")
      l.DrawLatex(85, 95, "Dee2")
    else:
      l.DrawLatex(5, 95, "Dee4")
      l.DrawLatex(85, 95, "Dee3")
    xo = -3
    sign = ("+", "-")[z == -1]
    l.DrawLatex(xo + 40, 85, sign + '1')
    l.DrawLatex(xo + 60, 85, sign + '9')
    l.DrawLatex(xo + 20, 65, sign + '2')
    l.DrawLatex(xo + 80, 65, sign + '8')
    l.DrawLatex(xo + 15, 45, sign + '3')
    l.DrawLatex(xo + 85, 45, sign + '7')
    l.DrawLatex(xo + 25, 20, sign + '4')
    l.DrawLatex(xo + 75, 20, sign + '6')
    l.DrawLatex(xo + 50, 10, sign + '5')

  def getEELines():
    xa1 = [50, 40, 40, 35, 35, 40, 40, 45, 45, 50]
    y1 = [0, 0, 3, 3, 15, 15, 30, 30, 39, 39]
    xa2 = [35, 25, 25, 20, 20, 15, 15, 13, 13, 8, 8, 10, 10, 20, 20, 30, 30, 35, 35, 40, 40, 41, 41, 42, 42, 43, 43, 45,
      45]
    y2 = [5, 5, 8, 8, 13, 13, 15, 15, 20, 20, 25, 25, 30, 30, 35, 35, 40, 40, 45, 45, 43, 43, 42, 42, 41, 41, 40, 40,
      39]
    xa3 = [8, 5, 5, 3, 3, 0, 0, 10, 10, 35, 35, 39, 39]
    y3 = [25, 25, 35, 35, 40, 40, 60, 60, 55, 55, 50, 50, 45]
    xa4 = [3, 3, 5, 5, 8, 8, 13, 13, 15, 15, 20, 20, 25, 25, 30, 30, 35, 35, 40, 40, 43, 43, 42, 42, 41, 41, 40, 40, 39,
      39]
    y4 = [60, 65, 65, 75, 75, 80, 80, 85, 85, 87, 87, 85, 85, 75, 75, 70, 70, 65, 65, 60, 60, 59, 59, 58, 58, 57, 57,
      55, 55, 50]
    xa5 = [20, 20, 25, 25, 35, 35, 40, 40, 50, 50, 45, 45, 42]
    y5 = [87, 92, 92, 95, 95, 97, 97, 100, 100, 61, 61, 60, 60]
    xa6 = [50, 60, 60, 65, 65, 60, 60, 55, 55, 50]
    xa7 = [65, 75, 75, 80, 80, 85, 85, 87, 87, 92, 92, 90, 90, 80, 80, 70, 70, 65, 65, 60, 60, 59, 59, 58, 58, 57, 57,
      55, 55]
    xa8 = [92, 95, 95, 97, 97, 100, 100, 90, 90, 65, 65, 61, 61]
    xa9 = [97, 97, 95, 95, 92, 92, 87, 87, 85, 85, 80, 80, 75, 75, 70, 70, 65, 65, 60, 60, 57, 57, 58, 58, 59, 59, 60,
      60, 61, 61]
    xa10 = [80, 80, 75, 75, 65, 65, 60, 60, 50, 50, 55, 55, 58]
    xb1 = [150, 140, 140, 135, 135, 140, 140, 145, 145, 150]
    xb2 = [135, 125, 125, 120, 120, 115, 115, 113, 113, 108, 108, 110, 110, 120, 120, 130, 130, 135, 135, 140, 140, 141,
      141, 142, 142, 143, 143, 145, 145]
    xb3 = [108, 105, 105, 103, 103, 100, 100, 110, 110, 135, 135, 139, 139]
    xb4 = [103, 103, 105, 105, 108, 108, 113, 113, 115, 115, 120, 120, 125, 125, 130, 130, 135, 135, 140, 140, 143, 143,
      142, 142, 141, 141, 140, 140, 139, 139]
    xb5 = [120, 120, 125, 125, 135, 135, 140, 140, 150, 150, 145, 145, 142]
    xb6 = [150, 160, 160, 165, 165, 160, 160, 155, 155, 150]
    xb7 = [165, 175, 175, 180, 180, 185, 185, 187, 187, 192, 192, 190, 190, 180, 180, 170, 170, 165, 165, 160, 160, 159,
      159, 158, 158, 157, 157, 155, 155]
    xb8 = [192, 195, 195, 197, 197, 200, 200, 190, 190, 165, 165, 161, 161]
    xb9 = [197, 197, 195, 195, 192, 192, 187, 187, 185, 185, 180, 180, 175, 175, 170, 170, 165, 165, 160, 160, 157, 157,
      158, 158, 159, 159, 160, 160, 161, 161]
    xb10 = [180, 180, 175, 175, 165, 165, 160, 160, 150, 150, 155, 155, 158]
    for x in (
        (xa1, y1), (xa2, y2), (xa3, y3), (xa4, y4), (xa5, y5), (xa6, y1), (xa7, y2), (xa8, y3), (xa9, y4), (xa10, y5),
    #               (xb1, y1), (xb2, y2), (xb3, y3), (xb4, y4), (xb5, y5),
    #               (xb6, y1), (xb7, y2), (xb8, y3), (xb9, y4), (xb10, y5),
    #              ([100, 100], [0, 100])
        ):
      yield x

  for p in getEELines():
    _EE_lines.append(DrawLine(p[0], p[1]))
  for i in _EE_lines:
    i.Draw()
  getEENumbers()


def getCanvasDbIds(data):
  return getCanvasHistDbIds(data)[0]


def getHistsDbIds(data):
  return getCanvasHistDbIds(data)[1:]


def getCanvasHistDbIds(data):
  # data has 'value' = ((dbid, value), (dbid, value), ...)
  from pfgutils.connection import ecalchannels
  from copy import deepcopy
  cur = ecalchannels.cursor()
  if 'values' not in data:
    logging.warning("Key 'values' not found in data")
    return None
  newdata = deepcopy(data)
  del newdata['values']
  newdata['eb'] = []
  newdata['ee+'] = []
  newdata['ee-'] = []
  # dump all channels
  # cur.execute("select dbid, det, ix, iy, iz, iphi, ieta from channels")
  # channels = {}
  # for row in cur.fetchall():
  #   channels[row[0]] = row[1:]
  for dbid, value in data['values']:
    # det, ix, iy, iz, iphi, ieta = channels[dbid]
    cur.execute("SELECT ieta, iphi, ix, iy, iz, det FROM channels WHERE dbId = ?", (dbid,))
    data = cur.fetchone()
    if 'EB' in data['det']:
      key = 'eb'
      x, y = data['iphi'], data['ieta']
    elif 'EE+' in data['det']:
      key = 'ee+'
      x, y = data['ix'], data['iy']
    elif 'EE-' in data['det']:
      key = 'ee-'
      x, y = data['ix'], data['iy']
    else:
      return
    newdata[key].append(((x, y), value))
  return getCanvasHist(newdata)


def getCanvasHist(data):
  ROOT.gStyle.SetOptStat(0)
  ROOT.gStyle.SetNumberContours(15)
  name = "Unnamed" if 'name' not in data else str(data['name'])
  title = "Unnamed" if 'name' not in data else str(data['title'])
  if name != "Unnamed" and title == "Unnamed":
    title = name
  ncontours = 100 if 'ncontours' not in data else int(data['ncontours'])

  if 'maximum' in data:
    if isinstance(data['maximum'], dict):
      maximum = dict((k, float(v)) for k, v in list(data['maximum'].items()))
    elif isinstance(data['maximum'], list) or isinstance(data['maximum'], tuple):
      maximum = dict(list(zip(('eb', 'ee-', 'ee+'), list(map(float, data['maximum'])))))
    else:
      maximum = dict(list(zip(('eb', 'ee-', 'ee+'), repeat(float(data['maximum']), 3))))
  else:
    maximum = None

  if 'minimum' in data:
    if isinstance(data['minimum'], dict):
      minimum = dict((k, float(v)) for k, v in list(data['minimum'].items()))
    elif isinstance(data['minimum'], list) or isinstance(data['minimum'], tuple):
      minimum = dict(list(zip(('eb', 'ee-', 'ee+'), list(map(float, data['minimum'])))))
    else:
      minimum = dict(list(zip(('eb', 'ee-', 'ee+'), repeat(float(data['minimum']), 3))))
  else:
    minimum = None

  if 'xlabel' in data:
    if isinstance(data['xlabel'], dict):
      xlabel = dict((k, str(v)) for k, v in list(data['xlabel'].items()))
    elif isinstance(data['xlabel'], list) or isinstance(data['xlabel'], tuple):
      xlabel = dict(list(zip(('eb', 'ee-', 'ee+'), list(map(str, data['xlabel'])))))
    else:
      xlabel = dict(list(zip(('eb', 'ee-', 'ee+'), repeat(str(data['xlabel']), 3))))
  else:
    xlabel = None

  if 'ylabel' in data:
    if isinstance(data['ylabel'], dict):
      ylabel = dict((k, str(v)) for k, v in list(data['ylabel'].items()))
    elif isinstance(data['ylabel'], list) or isinstance(data['ylabel'], tuple):
      ylabel = dict(list(zip(('eb', 'ee-', 'ee+'), list(map(str, data['ylabel'])))))
    else:
      ylabel = dict(list(zip(('eb', 'ee-', 'ee+'), repeat(str(data['ylabel']), 3))))
  else:
    ylabel = None

  for i in ('eb', 'ee-', 'ee+'):
    if i not in data:
      data[i] = []

  ROOT.gStyle.SetNumberContours(ncontours)
  c = ROOT.TCanvas(name, title)
  c.Divide(1, 2)

  # Fill histograms
  EB = ROOT.TH2D(name + "_EB", title + " EB", 360, 0, 360, 170, -85, 85)
  EE1 = ROOT.TH2D(name + "_EEm", title + " EE-", 100, 0, 100, 100, 0, 100)
  EE2 = ROOT.TH2D(name + "_EEp", title + " EE+", 100, 0, 100, 100, 0, 100)

  EE1.SetNdivisions(20, 'X')
  EE1.SetNdivisions(20, 'Y')
  EE2.SetNdivisions(20, 'X')
  EE2.SetNdivisions(20, 'Y')
  EB.SetNdivisions(18, 'X')
  EB.SetNdivisions(2, 'Y')

  for k, h in list({'eb': EB, 'ee-': EE1, 'ee+': EE2}.items()):
    if maximum:
      h.SetMaximum(maximum[k])

    if minimum:
      if not isinstance(minimum, list):
        h.SetMinimum(minimum[k])

    if ylabel:
      h.GetYaxis().SetTitle(ylabel[k])

    if xlabel:
      h.GetXaxis().SetTitle(xlabel[k])

  for det, (x, y), value in ECALDataYield({'eb': data['eb'], 'ee+': data['ee+'], 'ee-': data['ee-']}):
    if det == 'eb':
      if y > 0:
        y -= 1
      EB.Fill(x - 1, y, value)
    else:
      if det == 'ee+':
        EE2.Fill(x - 1, y - 1, value)
      else:
        EE1.Fill(x - 1, y - 1, value)

  # plot Barrel
  pad = c.cd(1)
  pad.SetCanvasSize(3600, 1710)
  EB.Draw('colz')
  _drawEBextra(c, 1)

  # Endcap
  pad0 = c.cd(2)
  pad0.Divide(2, 1)

  # Endcap z = -1
  pad1 = pad0.cd(1)
  pad1.SetCanvasSize(1000, 1000)

  EE1.Draw("colz")
  _drawEEextra(pad0, 1, -1)
  pad2 = pad0.cd(2)
  pad2.SetCanvasSize(1000, 1000)
  EE2.Draw("colz")
  _drawEEextra(pad0, 2, 1)

  for p in (pad, pad1, pad2):
    p.SetGridx(True)
    p.SetGridy(True)

  c.Update()
  ROOT.SetOwnership(EB, False)
  ROOT.SetOwnership(EE1, False)
  ROOT.SetOwnership(EE2, False)
  return c, EB, EE2, EE1


def ECALDataYield(data):
  for key in data.keys():
    for elem in data[key]:
      yield [key] + list(elem)
