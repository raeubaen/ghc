#!/usr/bin/env python



import ROOT
import argparse
import itertools
import logging
import re
import sys
from collections import OrderedDict

# noinspection PyUnresolvedReferences
import pfgutils.connection
import pfgutils.textile
import textile2html
from ghc_modules import Data
from ghc_modules.Plot import Plotter


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """
    Natural sorting function. Origin: https://stackoverflow.com/a/16090640
    :param s: data to sort
    :param _nsre: sorting regex
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

pfgutils.connection.connect(oracle=True, chanstat=True)

footer = """h1. Description of errors

h2. Description of errors for EB

h3. Dead pedestal  (DP)  :

* Gain 1 : MEAN <= 1 or RMS <= 0.2
* Gain 6 : MEAN <= 1 or RMS <= 0.4
* Gain 12: MEAN <= 1 or RMS <= 0.5

h3. Bad pedestal   (BP)  :

* abs(MEAN - 200) >= 30 and MEAN > 1

h3. Large RMS      (LR)  :

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS >= 1.1 and RMS < 3 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS >= 1.3 and RMS < 4 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS >= 2.1 and RMS < 6 and MEAN > 1)

h3. Very Large RMS (VLR) :

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS > 3 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS > 4 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS > 6 and MEAN > 1)

h2. Description of errors for EE

h3. Dead pedestal  (DP)  :

* Gain 1 : MEAN <= 1 or RMS <= 0.2
* Gain 6 : MEAN <= 1 or RMS <= 0.4
* Gain 12: MEAN <= 1 or RMS <= 0.5

h3. Bad pedestal   (BP)  :

* abs(MEAN - 200) >= 30 and MEAN > 1

h3. Large RMS      (LR)  :

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS >= 1.5 and RMS < 4 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS >= 2.0 and RMS < 5 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS >= 3.2 and RMS < 7 and MEAN > 1)

h3. Very Large RMS (VLR) :

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS > 4 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS > 5 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS > 7 and MEAN > 1)

h2. Description of HV OFF errors:

h3. Bad Voltage for G12 (BV):

* abs(RMS&#40;HVON) - RMS&#40;HVOFF)) < 0.2 and 170 <= MEAN&#40;HVON) <= 230

h2. Description of Test Pulse errors

h3. Dead TestPulse          (DTP):

* MEAN = 0

h3. Low TestPulse amplitude (STP):

* AVG = average mean for each subdetector (EB, EE)
* MEAN > 0 and MEAN < 0.5 * AVG

h3. Large TP amplitude      (LTP):

* MEAN > 1.5 * AVG

h2. Description of Laser Pulse errors:

* DLAMPL: MEAN <= 0
* SLAMPL: MEAN > 0 and MEAN < AVG * 0.1         # AVG per subdetector
* LLERRO: MEAN > AVG * 0.1 and RMS / MEAN > 0.1 # AVG per subdetector

h2. ECAL channel status:

*  0:  channel ok
*  1:  DAC settings problem, pedestal not in the design range
*  2:  channel with no laser, ok elsewhere
*  3:  noisy
*  4:  very noisy

p."""


def pairwise(iterable):
    # s -> (s1,s0), (s2,s1), (s3, s2), ...
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(b, a)


def getRMS(g, key):
    """
    Get RMS of a given value (key)
  
    :param g: GHC to collect stats from
    :type g: Data.Data
    :param key: what data to use
    :type key: string
  
    Query code found here: https://explainextended.com/2009/10/13/running-root-mean-square-sql-server/
    """

    sql = """WITH    nums AS
            (
            SELECT  value, ROW_NUMBER() OVER (ORDER BY dbid) AS rn
            FROM    values
            WHERE   keyid=(SELECT keyid FROM valuekeys WHERE key=%(key)s) AND ghc=%(ghc)s
            )
    SELECT  SQRT(AVG(POWER(np.value - nn.value, 2)))
    FROM    nums np
    JOIN    nums nn
    ON      nn.rn = np.rn + 1
    """
    g.cur.execute(sql, {'key': key, 'ghc': g.ghc_id})
    try:
        return round(g.cur.fetchone()[0], 3)
    except IndexError:
        return -1


def getDiff(this_ghc, prev_ghc, func, alt_func=None, lists=False, debug=False):
    """
    Return formatted  and (optionaly) lists of items present only in a or only in b
    :param debug: Enables debug logging
    :type debug: bool
    :param alt_func: alternative function to get number of items from this_ghc. Used only if prev_ghc==False
    :param func: lambda to use to get lists from a and b
    :param lists: Return lists or not
    :param Data.Data this_ghc: this_ghc
    :param Data.Data prev_ghc: prev_ghc
    :return: (str) | (str, tuple, tuple)
    """

    if prev_ghc is None:
        return "{0}".format(alt_func(this_ghc))

    a = func(this_ghc)
    if debug:
        logging.debug("This: %d/%d entries", len(set(a)), len(a))
    b = func(prev_ghc)
    if debug:
        logging.debug("Old: %d/%d entries", len(set(b)), len(b))

    only_this = set(a) - (set(a) & set(b))
    if debug:
        logging.debug("only_this: %d entries", len(only_this))
    only_prev = set(b) - (set(a) & set(b))
    if debug:
        logging.debug("only_prev: %d entries", len(only_prev))

    if lists:
        return r"\({0}^{{+{1}}}_{{-{2}}}\)".format(len(a), len(only_this), len(only_prev)), tuple(only_this), tuple(
            only_prev)
    else:
        return r"\({0}^{{+{1}}}_{{-{2}}}\)".format(len(a), len(only_this), len(only_prev))


def getGHCStats(this_ghc, prev_ghc=None):
    """
    Collect various statistics for a given GHC
  
    :param this_ghc: GHC to collect stats from
    :type this_ghc: Data.Data
    :param prev_ghc: GHC to compare to
    :type this_ghc: Data.Data
    :returns Dictionary
    :rtype dict
    """
    result = OrderedDict()
    td = {'PED_ON': 'Pedestals (HV ON)', 'PED_OFF': 'Pedestals (HV OFF)', 'ADC': 'Testpulse'}
    # print("  " + dbFile + " ===")
    for t in ("PED_ON", 'PED_OFF', 'ADC'):
        for gain in ("G1", "G6", "G12"):
            result["Active  channels {0} {1}".format(td[t], gain)] = \
                getDiff(this_ghc, prev_ghc,
                        lambda x: x.getActiveChannels(det='ALL', datatype='{0}_MEAN_{1}'.format(t, gain)),
                        lambda x: x.getNumOfActiveChannels(det='ALL', datatype='{0}_MEAN_{1}'.format(t, gain)),
                        False)

            result["Inactive channels {0} {1}".format(td[t], gain)] = \
                getDiff(this_ghc, prev_ghc,
                        lambda x: x.getInactiveChannels(det='ALL', datatype='{0}_MEAN_{1}'.format(t, gain)),
                        lambda x: x.getNumOfInactiveChannels(det='ALL', datatype='{0}_MEAN_{1}'.format(t, gain)),
                        False)

    result["Total Problematic channels"] = getDiff(this_ghc, prev_ghc, lambda x: x.getProblematicChannels(),
                                                   lambda x: x.getNumOfProblematicChannels(), False)

    result["Channels within design performance in G12"] = getDiff(this_ghc, prev_ghc,
                                                                  lambda x: x.getDesignChannels(),
                                                                  lambda x: x.getNumOfDesignChannels(), False)

    result["Noisy chanels in G12"] = getDiff(this_ghc, prev_ghc, lambda x: x.getChannelsWithFlag("LRG12"),
                                             lambda x: x.getNumChannelsWithFlag("LRG12"), False)

    result["Very noisy chanels in G12"] = getDiff(this_ghc, prev_ghc, lambda x: x.getChannelsWithFlag("VLRG12"),
                                                  lambda x: x.getNumChannelsWithFlag("VLRG12"), False)
    result["Pedestal rms ADC counts in G12"] = getRMS(this_ghc, 'PED_ON_RMS_G12')
    result["Pedestal rms ADC counts in G6"] = getRMS(this_ghc, 'PED_ON_RMS_G6')
    result["Pedestal rms ADC counts in G1"] = getRMS(this_ghc, 'PED_ON_RMS_G1')
    result["APD with bad or no connection to HV"] = getDiff(this_ghc, prev_ghc, lambda x: x.getChannelsWithFlag("BV%"),
                                                            lambda x: x.getNumChannelsWithFlag("BV%"), False)

    result["Dead channels due to LVR board problems"] = getDiff(this_ghc, prev_ghc,
                                                                lambda x: x.getChannelsWithFlag("DLAMPL"),
                                                                lambda x: x.getNumChannelsWithFlag("DLAMPL"), False)

    return result


def decode_flag(flag):
    """
    Print textile-formatted explanation (using HTML <abbr> tag) of a given flag
    :param flag: flag to explain
    :type flag: str
    :return:
    :rtype: str
    """
    if 'G' in flag:
        # pedestal/hv flag
        flag_type, gain = flag.split('G')
        x = {'DP': 'Dead Pedestal', 'BP': 'Bad Pedestal', 'LR': 'Large RMS', 'VLR': 'Very Large RMS',
             'BV': 'Bad Voltage',
             'DTP': 'Dead TestPulse', 'STP': 'Low TestPulse amplitude', 'LTP': 'Large TP amplitude'}
        if flag_type != 'BV':
            return '{0}({1} in Gain {2})'.format(flag, x[flag_type], gain)
        else:
            return '{0}({1})'.format(flag, x[flag_type])
    else:
        x = {'DLAMPL': 'Dead laser', 'SLAMPL': 'Low Laser Amplitude', 'LLERRO': 'Large RMS'}
        return '{0}({1})'.format(flag, x[flag])


def format_flag(bad_channel, this_ghc, style, flag):
    """
    For a given flag and channel, print description of this flag and relevant parameter(s)
    :param bad_channel: channel ID
    :type bad_channel: int
    :param this_ghc: identifier of GHC to get data
    :type this_ghc: str
    :param style: textile markup to use for this flag (one of '+', '-', '')
    :type style: str
    :param flag: abbreviated flag name
    :type flag: str
    :rtype: str
    """
    # is_ee = Data.getSubDetector(bad_channel) == 'EE'
    if style == '+':
        res = '%(added){0}%'.format(decode_flag(flag))
    else:
        res = '{0}{1}{0}'.format(style, decode_flag(flag))
    if style != '-':
        g = data[this_ghc]
        if flag.startswith('DP') or flag.startswith('BP') or flag.startswith('LR') or flag.startswith('VLR'):
            # Pedestal error
            gain = 'G' + flag.split('G', 1)[1]
            mean = float(g.getChannelData(bad_channel, key='PED_ON_MEAN_{0}'.format(gain)))
            rms = float(g.getChannelData(bad_channel, key='PED_ON_RMS_{0}'.format(gain)))
            res += ' ({0:.2f} &#177; {1:.2f})'.format(mean, rms)

        if flag.startswith('DTP') or flag.startswith('STP') or flag.startswith('LTP'):
            gain = 'G' + flag.split('G', 1)[1]
            mean = float(g.getChannelData(bad_channel, key='ADC_MEAN_{0}'.format(gain)))
            rms = float(g.getChannelData(bad_channel, key='ADC_RMS_{0}'.format(gain)))
            res += ' ({0:.2f} &#177; {1:.2f})'.format(mean, rms)

        if flag.startswith('BV'):
            gain = 'G' + flag.split('G', 1)[1]
            mean_on = float(g.getChannelData(bad_channel, key='PED_ON_RMS_{0}'.format(gain)))
            mean_off = float(g.getChannelData(bad_channel, key='PED_OFF_RMS_{0}'.format(gain)))
            res += ' (ON: {0:.2f}, OFF: {1:.2f})'.format(mean_on, mean_off)

        if flag in ('DLAMPL', 'SLAMPL', 'LLERRO'):
            mean = float(g.getChannelData(bad_channel, key='APD_MEAN'))
            rms = float(g.getChannelData(bad_channel, key='APD_RMS'))
            res += ' ({0:.2f} &#177; {1:.2f})'.format(mean, rms)

    return res


def format_channel(chan, this_ghc, prev_ghc=None):
    """
    Create textual representation of state of a given channel, optionaly - compared to a different GHC
  
    :param chan: channel
    :type chan: int
    :param this_ghc: GHC to get data from
    :type this_ghc: str
    :param prev_ghc: GHC to compare to
    :type prev_ghc: str|None
    :return: formatted string and indication if channel flags changed between GHCs
    :rtype: (str, bool)
    """

    this_flags = flags_for_channel[chan].get(this_ghc)
    if this_flags is not None:
        cell_text = ", ".join((format_flag(chan, this_ghc, '', flag) for flag in this_flags))
    else:
        this_flags = []
        if bad_channel in data[this_ghc].getMissedChannels():
            return "Missed channel", True
        else:
            cell_text = "OK" if prev_ghc is None else "OK: "

    # If we are not comparing (either just printing 1st column - prev_ghc is None - or just dumping everything
    if prev_ghc is None:
        return cell_text, False  # doesn't matter what is returned for the 2nd argument

    prev_flags = flags_for_channel[chan].get(prev_ghc) or []

    all_flags = set(this_flags) | set(prev_flags)
    added = set(this_flags) - set(prev_flags)
    fixed = set(prev_flags) - set(this_flags)

    cell = []
    for flag in sorted(all_flags, key=natural_sort_key):
        if flag in added:
            cell.append(format_flag(chan, this_ghc, '+', flag))
        else:
            if flag in fixed:
                cell.append(format_flag(chan, this_ghc, '-', flag))
            else:
                cell.append(format_flag(chan, this_ghc, '', flag))

    if not this_flags:  # cell_text is "OK:<spc>"
        cell_text += ", ".join(cell)
    else:
        cell_text = ", ".join(cell)

    flags_changed = bool(added) or bool(fixed)

    return cell_text, flags_changed


def getFlagStats(this_ghc, prev_ghc=None):
    """
    Prints how many channels gained/lost each flag when comparing prev_data and this_data
    :param prev_ghc: old GHC
    :type prev_ghc: Data.Data | None
    :param this_ghc: new GHC
    :type this_ghc: Data.Data
    :rtype: dict
    """

    res = OrderedDict()

    for f in itertools.chain(Data.Data.PEDESTAL_FLAGS, Data.Data.HV_FLAGS, Data.Data.TESTPULSE_FLAGS):
        for g in ('G1', 'G6', 'G12'):
            flag = "{0}{1}".format(f, g)
            res[flag] = {}
            for d in ('EB', 'EE'):
                res[flag][d] = getDiff(this_ghc, prev_ghc, lambda x: x.getChannelsWithFlag(flag, det=d),
                                       lambda x: x.getNumChannelsWithFlag(flag, det=d))

    return res


import errno, os
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

parser = argparse.ArgumentParser()
parser.add_argument('checks', metavar="ghc", nargs="+", help="GHC(s) to analyse.")
parser.add_argument('-O', "--outdir", help="Output directory; pass '-' to print to stdout", dest="outdir",
                    action="store")
parser.add_argument('-v', "--verbose", help="Enable more verbose output.", dest="verbose", action="store_true")
parser.add_argument('-k', "--keep-flagged", help="Keep channels with channeldb flag >= 3", dest="keep",
                    action="store_true")
group = parser.add_mutually_exclusive_group()
group.add_argument('-c', "--changed", help="Only output channels with flag changes", dest='changed',
                   action="store_true")
group.add_argument('-u', "--unchanged", help="Only output channels without flag changes", dest='unchanged',
                   action="store_true")
args = parser.parse_args()

if not (args.changed or args.unchanged):
    mode = "all"
    header_text = ""
else:
    if args.changed:
        mode = "changed"
        header_text = "- Only changed channels"
    else:
        mode = "unchanged"
        header_text = "- Only unchanged channels"

if args.outdir != '-':
    if not args.outdir:
        args.outdir = "compare_" + "_".join(args.checks)
 
    mkdir_p(args.outdir)
    outfilen = os.path.join(args.outdir, "index.textile")
    logging.info("Will print to {0}".format(outfilen))
        
    try:
        outfile = open(outfilen, "w")
    except Exception as e:
        print("Unable to open file {0} for writing!".format(outfilen))
        print("Error message:", e.message)
        outfile = sys.stdout
else:
    outfile = sys.stdout

data = {}


for ghc_id in args.checks:
    logging.info("Reading GHC " + ghc_id + " ...")
    g = Data.Data(ghc_id, args.keep)
    if not g.isClassified:
        logging.error("GHC %s not classified!", ghc_id)
        continue

    data[ghc_id] = g
    logging.info("Finished " + ghc_id + ".")

args.checks = sorted(list(data.keys()), key=natural_sort_key)

headers = ["&nbsp;"]
headers.extend(args.checks)

logging.info("Compare GHC runs ...")
stats = getGHCStats(data[args.checks[0]], None)
tab = [[x, stats[x]] for x in list(stats.keys())]
for this_ghc, prev_ghc in pairwise(args.checks):
    stats = getGHCStats(data[this_ghc], data[prev_ghc])
    for i, x in enumerate(stats.values()):
        tab[i].append(x)

print(pfgutils.textile.table(headers, tab, caption="GHC statistics"), file=outfile)

logging.info("Compare flags ...")
fancy_headers = [[(x, 1) if x.startswith('&') else (x, 2) for x in headers],
                 [("Subdetector", 1)]]
fancy_headers[1].extend(itertools.chain(*itertools.repeat((('EB', 1), ('EE', 1)), len(args.checks))))

stats = getFlagStats(data[args.checks[0]], None)
tab = [[x, stats[x]['EB'], stats[x]['EE']] for x in list(stats.keys())]
for this_ghc, prev_ghc in pairwise(args.checks):
    stats = getFlagStats(data[this_ghc], data[prev_ghc])
    for i, x in enumerate(stats.keys()):
        tab[i].extend([stats[x]['EB'], stats[x]['EE']])

print(pfgutils.textile.fancy_table(fancy_headers, tab, caption="Flag statistics"), file=outfile)

plotr = {}

flags_for_channel = {}
for dbFile in data:
    g = data[dbFile]
    plotr[dbFile] = Plotter(g)
    for bad_channel in g.getProblematicChannels():
        flags = g.getFlagsForChannel(bad_channel)
        if bad_channel not in flags_for_channel:
            flags_for_channel[bad_channel] = {}
        flags_for_channel[bad_channel][dbFile] = sorted(flags, key=natural_sort_key)

ROOT.gROOT.SetBatch(True)
c = ROOT.TCanvas()
c.cd()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetLabelSize(0.017, "X")
ROOT.gStyle.SetLabelSize(0.017, "Y")
ROOT.gPad.SetRightMargin(0.2)

ext = "png"

for plottype in ('mean', 'RMS'):
    for g in ("G1", "G6", "G12"):
        for d in ("EB", "EE"):
            if all(d.has_ped_hvon for d in list(data.values())):
                hists = []
                legend = ROOT.TLegend(0.8, 0.8, 1.0, 1.0)
                for i, dbFile in enumerate(plotr.keys()):
                    plotter = plotr[dbFile]
                    ### 1D plots
                    h = plotter.get1DHistogram(key=("PED_ON_{0}_{1}".format(plottype, g)).upper(), det=d,
                                               name="Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV ON"))
                    h.SetLineColor(ROOT.kBlack + i + 1)
                    ROOT.SetOwnership(h, False)
                    hists.append(h)
                    legend.AddEntry(h, dbFile, "L")
                # c.Clear()
                hAxis = ROOT.TH1F("axis", "Pedestal {0}, gain {1} ({2}), {3}".format(plottype, g, "HV ON", d),
                                  hists[0].GetNbinsX(), hists[0].GetXaxis().GetXmin(),
                                  hists[0].GetXaxis().GetXmax())
                hAxis.SetMinimum(1)
                hAxis.SetMaximum(max(x.GetMaximum() for x in hists) * 1.1)
                hAxis.Draw("")
                c.SetLogy()

                for h in hists:
                    h.Draw("SAME")

                legend.Draw()
                c.SaveAs("{4}/ped_on_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext, args.outdir))
                print(pfgutils.textile.img("ped_on_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext)) + "\n",
                      file=outfile)

            if all(d.has_ped_hvoff for d in list(data.values())):
                hists = []
                legend = ROOT.TLegend(0.8, 0.8, 1.0, 1.0)
                for i, dbFile in enumerate(plotr.keys()):
                    plotter = plotr[dbFile]
                    ### 1D plots
                    h = plotter.get1DHistogram(key=("PED_OFF_{0}_{1}".format(plottype, g)).upper(), det=d,
                                               name="Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV OFF"))
                    h.SetLineColor(ROOT.kBlack + i + 1)
                    ROOT.SetOwnership(h, False)
                    hists.append(h)
                    legend.AddEntry(h, dbFile, "L")
                c.Clear()
                hAxis = ROOT.TH1F("axis", "Pedestal {0}, gain {1} ({2}), {3}".format(plottype, g, "HV OFF", d),
                                  hists[0].GetNbinsX(), hists[0].GetXaxis().GetXmin(),
                                  hists[0].GetXaxis().GetXmax())
                hAxis.SetMinimum(1)
                hAxis.SetMaximum(max(x.GetMaximum() for x in hists) * 1.1)
                hAxis.Draw("")
                for h in hists:
                    h.Draw("SAME")

                legend.Draw()
                c.SaveAs("{4}/ped_off_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext, args.outdir))
                print(pfgutils.textile.img("ped_off_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext)) + "\n",
                      file=outfile)

            if all(d.has_testpulse for d in list(data.values())):
                hists = []
                legend = ROOT.TLegend(0.8, 0.8, 1.0, 1.0)
                for i, dbFile in enumerate(plotr.keys()):
                    plotter = plotr[dbFile]
                    ### 1D plots
                    h = plotter.get1DHistogram(key=("ADC_{0}_{1}".format(plottype, g)).upper(), det=d,
                                               name="Test Pulse {0}, gain {1}".format(plottype, g))
                    h.SetLineColor(ROOT.kBlack + i + 1)
                    ROOT.SetOwnership(h, False)
                    hists.append(h)
                    legend.AddEntry(h, dbFile, "L")
                c.Clear()
                hAxis = ROOT.TH1F("axis", "Test Pulse {0}, gain {1}, {2}".format(plottype, g, d), hists[0].GetNbinsX(),
                                  hists[0].GetXaxis().GetXmin(),
                                  hists[0].GetXaxis().GetXmax())
                hAxis.SetMinimum(1)
                hAxis.SetMaximum(max(x.GetMaximum() for x in hists) * 1.1)
                hAxis.Draw("")
                for h in hists:
                    h.Draw("SAME")

                legend.Draw()
                c.SaveAs("{4}/tp_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext, args.outdir))
                print(pfgutils.textile.img("tp_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext)) + "\n",
                      file=outfile)

    if all(d.has_laser for d in list(data.values())):
        for d in ("EB", "EE"):
            hists = []
            legend = ROOT.TLegend(0.8, 0.8, 1.0, 1.0)
            for i, dbFile in enumerate(plotr.keys()):
                plotter = plotr[dbFile]
                ### 1D plots
                h = plotter.get1DHistogram(key=("APD_{0}".format(plottype)).upper(), det=d,
                                           name="Laser {0} ({1})".format(plottype, args.lasertable))
                h.SetLineColor(ROOT.kBlack + i + 1)
                ROOT.SetOwnership(h, False)
                hists.append(h)
                legend.AddEntry(h, dbFile, "L")
            c.Clear()
            hAxis = ROOT.TH1F("axis", "Laser {0} ({1}), {2}".format(plottype, args.lasertable, d), hists[0].GetNbinsX(),
                              hists[0].GetXaxis().GetXmin(),
                              hists[0].GetXaxis().GetXmax())
            hAxis.SetMinimum(min(x.GetMinimum() for x in hists))
            hAxis.SetMaximum(max(x.GetMaximum() for x in hists) * 1.1)
            hAxis.Draw("")
            for h in hists:
                h.Draw("SAME")

            legend.Draw()
            c.SaveAs("{4}/laser_{1}_{2}.1D.{3}".format('', plottype.upper(), d, ext, args.outdir))
            print(pfgutils.textile.img("laser_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext)) + "\n",
                  file=outfile)

            hists = []
            legend = ROOT.TLegend(0.8, 0.8, 1.0, 1.0)
            for i, dbFile in enumerate(plotr.keys()):
                plotter = plotr[dbFile]
                ### 1D plots
                h = plotter.get1DHistogram(key="APD_OVER_PN_{0}".format(plottype), det=d,
                                           name="APD/PN {0} ({1})".format(plottype, args.lasertable))
                h.SetLineColor(ROOT.kBlack + i + 1)
                ROOT.SetOwnership(h, False)
                hists.append(h)
                legend.AddEntry(h, dbFile, "L")
            c.Clear()
            hAxis = ROOT.TH1F("axis", "APD/PN {0} ({1}), {2}".format(plottype, args.lasertable, d), hists[0].GetNbinsX(),
                              hists[0].GetXaxis().GetXmin(),
                              hists[0].GetXaxis().GetXmax())
            hAxis.SetMinimum(min(x.GetMinimum() for x in hists))
            hAxis.SetMaximum(max(x.GetMaximum() for x in hists) * 1.1)
            hAxis.Draw("")
            for h in hists:
                h.Draw("SAME")

            legend.Draw()
            c.SaveAs("{4}/laser_ratio_{1}_{2}.1D.{3}".format('', plottype.upper(), d, ext, args.outdir))
            print(pfgutils.textile.img("laser_ratio_{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext)) + "\n",
                  file=outfile)

if args.verbose:
    # c = psycopg2.connect("host='128.142.136.43' dbname='ecalchannelstatus' user='pfgreadonly' password='ecalpfg'")
    cur = pfgutils.connection.ecalchannelstatus.cursor()

    header_ee = False
    outfile.write("table(sortable).\n")
    outfile.write("|=. Channel flags (EB)%s. Channels with status > 3 are not shown.\n" % header_text)
    # outfile.write("|^.")
    outfile.write("|_. Channel |_. FED |_. ECAL channel status |_(sorttable_nosort). " +
                  "|_(sorttable_nosort). ".join(
                      ["{0} (\"Report\":../{0}/report.html)".format(x) for x in args.checks]) + " |\n")
    # outfile.write("|-.")
    for bad_channel in sorted(flags_for_channel):
        is_ee = Data.getSubDetector(bad_channel) == 'EE'
        if is_ee and not header_ee:
            header_ee = True
            outfile.write("\ntable(sortable).\n")
            outfile.write("|=. Channel flags (EE)%s. Channels with status > 3 are not shown.\n" % header_text)
            outfile.write(
                "|_. Channel |_. FED |_. ECAL channel status |_(sorttable_nosort). " +
                "|_(sorttable_nosort). ".join(
                    ["{0} (\"Report\":../{0}/report.html)".format(x) for x in args.checks]) + " |\n")

        cur.execute("SELECT status FROM ecalchannelstatus WHERE dbid=%s and \
            iov = (select max(iov) from ecalchannelstatus) and tag=%s", (bad_channel, 'EcalChannelStatus_v1_hlt'))

        a = cur.fetchone()
        if a:
            db_flag = a[0]
        else:
            db_flag = 0

        if db_flag >= 3 and not args.keep:
            continue

        row = ("| %d | %s | %d |" % (bad_channel, Data.getDetSM(bad_channel), db_flag))

        cell, row_changed = format_channel(bad_channel, args.checks[0], None)
        if cell.startswith('OK'):
            row += '(healthy).'
        elif cell.startswith('Missed'):
            row += '(missed).'

        row += ' '

        row += cell + " |"

        for this_ghc, prev_ghc in pairwise(args.checks):
            cell, flag = format_channel(bad_channel, this_ghc, prev_ghc)

            if cell.startswith('OK'):
                row += '(healthy).'
            elif cell.startswith('Missed'):
                row += '(missed).'

            row += ' '

            row += cell + " |"
            row_changed |= flag

        if (mode == "all" or mode == "changed") and row_changed:
            outfile.write(row.strip() + "\n")

        if (mode == "all" or mode == "unchanged") and not row_changed:
            outfile.write(row.strip() + "\n")

outfile.write("\n" + footer)
outfile.close()

textile2html.convert(outfilen)
