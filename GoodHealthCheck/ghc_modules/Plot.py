import ROOT
import logging

from pfgutils import plotECAL


class Plotter(object):
  def __init__(self, data):
    self.data = data

  def get1DHistogram(self, name, key, det, dimx=None):
    """
    Return TH1F histogram.
    Parameters:
    name    : title of histogram.
    key     : key of data to be used
    det     : "EB" | "EE"
    dimx    : range of X axis. Default is ((150, 250), (0, 5))[RMS]
    """
    logging.debug("Plot 1D histogram named \"{0}\" of value {1} in detector {2}".format(name, key, det))
    use_rms = 'RMS' in key

    activech = self.data.getActiveChannels(key, det=det)
    if not activech:
      logging.warning(f'empty list of active channels: {key}')
      return None
    self.data.getAllChannelData()###FIND GOOD SPOT TO CALL ONCE
    if dimx is None:
      if key.startswith('ADC'):
        if det == "EB":
          dimx = ((1000, 3000), (0, 20))[use_rms]
        else:
          dimx = ((1000, 4000), (0, 20))[use_rms]
      elif key.startswith('PED'):
        dimx = ((150, 250), (0, 5))[use_rms]
      else:  # Laser
        if "OVER" in key:
          dimx = ((0, 5), (0, 0.1))[use_rms]
        else:
          dimx = ((0, 6000), (0, 5))[use_rms]

    hist = ROOT.TH1F(name, name, 100, dimx[0], dimx[1])
    hist.SetXTitle("{0} (ADC counts)".format(("Mean", "RMS")[use_rms]))
    for ch in activech:
      val = None
      try:
        val = self.data.getChannelData(ch, key=key)
        if val is None:
            logging.warning(f'Channel {ch} returned None for key {key}')
        hist.Fill(float(val))
      except Exception:
        if val is None:
          logging.exception("Cannot get value from channel %s and key %s!".format(ch, key))
        else:
          logging.exception("Cannot fill value %s!", val)

    return hist

  def get2DHistogram(self, name, key):
    """
      Returns TH2F histogram.
      Parameters:
        key      : data[key] which will be used
        name     : title of histogram.
    """
    use_rms = 'RMS' in key
    gain = key.split("_")[-1]
    if "G" not in gain:
      # laser
      if key.split("_")[1] == "OVER":
        gain = 'APD/PN'
      else:
        gain = 'Laser'

    lim = {}

    if key.startswith('PED_ON'):
      lim['ee'] = {True: {"G1": (0.3, 0.8), "G6": (0.7, 1.5), "G12": (1.2, 3.4)},
                   False: {"G1": (160, 240), "G6": (160, 240), "G12": (160, 240)}}
      lim['eb'] = {True: {"G1": (0.3, 0.8), "G6": (0.4, 1.1), "G12": (0.8, 2.2)},
                   False: {"G1": (160, 240), "G6": (160, 240), "G12": (160, 240)}}
    elif key.startswith('PED_OFF'):
      lim['ee'] = {True: {"G1": (0.3, 0.8), "G6": (0.7, 1.5), "G12": (1.2, 3.0)},
                   False: {"G1": (160, 240), "G6": (160, 240), "G12": (160, 240)}}
      lim['eb'] = {True: {"G1": (0.3, 0.8), "G6": (0.5, 2.5), "G12": (2.2, 3.5)},
                   False: {"G1": (160, 240), "G6": (160, 240), "G12": (160, 240)}}
    elif key.startswith('ADC'):
      lim['ee'] = {True: {"G1": (0, 12), "G6": (0, 6), "G12": (0, 6)},
                   False: {"G1": (2000, 3500), "G6": (2000, 3000), "G12": (2000, 3000)}}
      lim['eb'] = {True: {"G1": (0, 10), "G6": (0, 4), "G12": (0, 3)},
                   False: {"G1": (1400, 3000), "G6": (1400, 3000), "G12": (1400, 3000)}}
    else:
      lim['ee'] = {True: {"Laser": (0, 60), 'APD/PN': (0, 0.05)},
                   False: {"Laser": (0, 2000), 'APD/PN': (0, 2.5)}}
      lim['eb'] = {True: {"Laser": (0, 50), 'APD/PN': (0, 0.06)}, False: {"Laser": (0, 2000), 'APD/PN': (0, 3)}}

    activech = self.data.getActiveChannels(key)

    if not activech:
      logging.warning(f'empty list of active channels: {key}')
      return 
    self.data.getAllChannelData()
    hist = {'name': name, 'title': name, 'values': [],
            'minimum': {'ee-': lim['ee'][use_rms][gain][0], 'ee+': lim['ee'][use_rms][gain][0],
                        'eb': lim['eb'][use_rms][gain][0]},
            'maximum': {'ee-': lim['ee'][use_rms][gain][1], 'ee+': lim['ee'][use_rms][gain][1],
                        'eb': lim['eb'][use_rms][gain][1]},
            'xlabel': {'ee-': 'iX+100', 'ee+': 'iX', 'eb': 'i#phi'},
            'ylabel': {'ee-': 'iY', 'ee+': 'iY', 'eb': 'i#eta'}}

    for ch in activech:
      try:
        val = self.data.getChannelData(ch, key=key)
        if val is None:
            logging.warning(f'Channel {ch} returned None for key {key}')
        hist['values'].append([ch, float(val)])
      except Exception:
        if 'val' not in locals():
          logging.exception("Cannot get value from channel %s and key %s!".format(ch, key))
        else:
          logging.exception("Cannot fill value %s!", val)
    return plotECAL.getCanvasDbIds(hist)
    #return hist

  @staticmethod
  def saveHistogram(histogram, filename):
    """
      Save <histogram> (TH1F or TCanvas) into filename according to <plottype>
      plottype = 'EE' | 'EB'
    """
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    try:
      if not histogram:
        logging.warning(f'Histogram is None for {filename}')
        return
      if isinstance(histogram, ROOT.TCanvas):  # type(histogram) is ROOT.TCanvas:
        c = histogram
#        # return
#        histogram.Draw("colz")
#        c.SetGridx(True)
#        c.SetGridy(True)
#        ROOT.gStyle.SetOptStat("e")
#        ROOT.gStyle.SetTickLength(0.01, "xy")
#        if plottype == "EB":
#            drawEBNumbers()
#        elif plottype == "EE":
#            c.SetCanvasSize(1000, 500)
#            lines = []
#            for p in getEELines():
#                lines.append(DrawLine(p[0], p[1]))
#            for i in lines:
#                i.Draw()
#            getEENumbers()
      else:
        c = ROOT.TCanvas()
        c.SetLogy()
        ROOT.gStyle.SetLabelSize(0.017, "X")
        ROOT.gStyle.SetLabelSize(0.017, "Y")
        histogram.Draw()
        ROOT.gStyle.SetOptStat("emruo")
        c.Update()

      c.SaveAs(filename)
      return True
    except Exception:
      logging.exception("Cannot save '%s'into %s".format(repr(histogram), filename))
      return False
