#!/usr/bin/env python
# coding=utf-8
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import argparse
import codecs
import copy
import datetime
import itertools
import logging
import os
import sys
from collections import OrderedDict

import textile2html
from ghc_modules import Data
from ghc_modules.Plot import Plotter
from pfgutils import textile
from pfgutils.Settings import max_good_status

import pfgutils.connection

startts = datetime.datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument('ghc_id', help="ID of this GHC", metavar="ghc")
parser.add_argument('-c', '--dbstr', choices=['oracle', 'files'], help="Data source (oracle|files)",
                    dest='dbstr', default="oracle")
parser.add_argument('-pon', help="Pedestal HV ON  runs numbers or list of files", dest='pon_runs')
parser.add_argument('-poff', help="Pedestal HV OFF runs numbers or list of files", dest='poff_runs')
parser.add_argument('-tp', help="Test Pulse runs numbers or list of files", dest='tp_runs')
parser.add_argument('-l', help="Laser runs or list of files", dest='l_runs')
parser.add_argument('-lt', '--lasertable', help="Laser table to use in Oracle DB", dest='lasertable',
                    default="MON_LASER_BLUE_DAT", metavar="TABLE")
parser.add_argument('-o', '--output', help="Results directory (default: <ghc_id> or <ghc_id>_keep)", dest='output',
                    metavar="DIRECTORY")
parser.add_argument('-r', '--redo', help="Redo existing GHC. Specify twice to re-classify channels.", dest='redo',
                    action='count')
parser.add_argument('--csv', help="Create csv file with a list of problematic channels", dest='csv',
                    action="store_true")
parser.add_argument('-k', "--keep-flagged", help="Keep channels with channeldb flag > {0}".format(max_good_status),
                    dest="keep", action="store_true")
parser.add_argument('-f', "--format", help="Image format", dest='imgformat', default="png", metavar="FORMAT")
parser.add_argument('-q', "--quiet", help="Don't print summary table with problematic channels", action="store_false",
                   dest='verbose')
parser.add_argument('-np', '--no-plots', help="Don't make plots", action="store_true", dest='noplots')
# TODO: Remove me when done
# parser.add_argument('--expert-mode', help=argparse.SUPPRESS, action="store_true", dest='expert')
parser.add_argument("--debug", help="Enable more verbose logging", action="store_const", const=logging.DEBUG,
                    default=logging.INFO, dest="loglevel")
args = parser.parse_args()

sys.argv = []

if args.output is None:
    args.output = args.ghc_id + ('_keep' if args.keep else '')

# if args.expert:
#     # logging.warning("Expert mode enabled, overriding command-line switches!")
#     args.imgformat = 'png'
#     args.verbose = True
#     args.noplots = False
#     args.csv = False
#     args.redo = 1
#     args.output = args.ghc_id
#     args.dbstr = "oracle"
#     args.keep = False

logger = logging.getLogger()
fh = logging.FileHandler(args.output + '.log', mode='w')
formatter = logging.Formatter('[%(levelname)s] %(message)s')
fh.setFormatter(formatter)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

logger.setLevel(args.loglevel)

ext = args.imgformat

if not args.output:
    outputdir = "RESULTS"
else:
    outputdir = args.output
if not os.path.exists(outputdir):
    os.mkdir(outputdir)

log_textile = codecs.open(os.path.join(outputdir, 'index.textile'), 'w', encoding='UTF-8')

header_count = {1: 0, 2: 0, 3: 0}

def header(text, level=1, name=None):
    header_count[level] += 1

    if name is None:
        name = "h{0}_{1}".format(level, header_count[level])

    if name != "top":
        return "h{1}. {0} <a name=\"{2}\"/> <a href=\"#top\">↑</a>\n".format(text, level, name)
    else:
        return "h1{{text-align: center}}. {0} <a name=\"{1}\"/>\n".format(text, name)


logging.info("GoodHealthCheck %s start", args.ghc_id)
GHC = Data.Data(args.ghc_id, args.keep)

if not GHC.can_redo and (args.redo is not None):
    print(GHC.can_redo)
    print(args.redo)
    logging.critical("No data found for GHC %s, aborting", args.ghc_id)
    exit(1)

if args.redo is None:
    if args.dbstr == "files":
        logging.warning("The data will be read from files!")
    else:
        logging.info("Loading data from Oracle database")
    source = args.dbstr

    if args.pon_runs is not None:
        logging.info("Pedestals with HV on...")
        GHC.readData(source, runs=args.pon_runs.split(), data_type="pedestal_hvon")
    if args.poff_runs is not None:
        logging.info("Pedestals with HV off...")
        GHC.readData(source, runs=args.poff_runs.split(), data_type="pedestal_hvoff")
    if args.tp_runs is not None:
        logging.info("Test pulse...")
        GHC.readData(source, runs=args.tp_runs.split(), data_type="testpulse")
    if args.l_runs is not None:
        logging.info("Laser...")
        GHC.readData(source, runs=args.l_runs.split(), data_type="laser", lasertable=args.lasertable)

if args.redo == 2:
    logging.warning("Channels will be reclassified")
    GHC.resetFlags()
GHC.classifyChannels()

logging.info("Creating report file")
print(header("GoodHealthCheck #{0}".format(args.ghc_id), 1, "top"), file=log_textile)
print("", file=log_textile)

if not args.keep:
    print("Channels with ecal channel status > {0} were removed. ".format(max_good_status), file=log_textile)
    print("Click \"here\":../{0}_keep/report.html to view report with all channels in.".format(args.ghc_id), file=log_textile)
    print("", file=log_textile)
else:
    print("Channels with ecal channel status > {0} were kept. ".format(max_good_status), file=log_textile)
    print("Click \"here\":../{0}/report.html to view report without these channels.".format(args.ghc_id), file=log_textile)
    print("", file=log_textile)

print(header("Runs", 2), file=log_textile)
print("", file=log_textile)
print("|_. Run type |_. Gain 1 |_. Gain 6 |_. Gain 12 |", file=log_textile)
runs = GHC.get_runs()

for run_type in ('pedestal_hvon', 'pedestal_hvoff', 'testpulse'):
    print("|", {'pedestal_hvon': "Pedestals, HV on",
                                'pedestal_hvoff': "Pedestals, HV off", 'testpulse': "Test pulse"}[run_type], "|", end=' ', file=log_textile)
    for gain in ('G1', 'G6', 'G12'):
        try:
            run = runs[run_type][gain]
        except KeyError:
            run = "-"

        print(run, "|", end=' ', file=log_textile)

    print("", file=log_textile)


def mkImgLink(url):
    return "!{{width: 300px;}}{0}!:{0}".format(url)


def print_lines(width=300, first=None):
    if first is not None:
        print("|:\\{0}. {1} | {2} |".format(len(lines[0]), width, first), file=log_textile)
    else:
        print("|:\\{0}. {1}".format(len(lines[0]), width), file=log_textile)

    for line in lines:
        print("| " + " | ".join(line) + " |", file=log_textile)


print("", file=log_textile)
print(header("PEDESTAL ANALYSIS"), file=log_textile)
if GHC.has_ped_hvon:

    for d in ["EB", "EE"]:
        print(header("PEDESTAL {0} ANALYSIS".format(d), 2), file=log_textile)
        print("", file=log_textile)
        lines = (["Missing channels"], ["Active  channels"])

        for g in ("G1", "G6", "G12"):
            act = GHC.getNumOfActiveChannels(d, 'PED_ON_MEAN_' + g)
            lines[0].append("{0}".format((61200, 14648)[d == "EE"] - act))
            lines[1].append("{0}".format(act))

        print("|=. Channel statistics ({0})".format(d), file=log_textile)
        print("|_. &nbsp; |_. Gain 1 |_. Gain 6 |_. Gain 12 |", file=log_textile)
        print_lines(150, 180)
        print("", file=log_textile)

        print("|=. Classes of pedestal problematic channels", file=log_textile)
        print("|_. {classn:41s} |_. {empty:3s} |_. {tags:21s} |".format(
            classn="&nbsp;",
            empty="Count", tags="Short name"), file=log_textile)
        for k in ["G1", "G6", "G12"]:
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Dead pedestal channels",
                                                                          GHC.getNumChannelsWithFlag("DP" + k, det=d),
                                                                          "DP" + k), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Pedestal mean outside [170,230]",
                                                                          GHC.getNumChannelsWithFlag("BP" + k, det=d),
                                                                          "BP" + k), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Large RMS (noisy channels)",
                                                                          GHC.getNumChannelsWithFlag("LR" + k, det=d),
                                                                          "LR" + k), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Very large RMS (very noisy channels)",
                                                                          GHC.getNumChannelsWithFlag("VLR" + k, det=d),
                                                                          "VLR" + k, d), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Bad pedestal and noisy channels",
                                                                          GHC.getNumChannelsWithFlag(
                                                                              ["BP" + k, "LR" + k],
                                                                              det=d),
                                                                          "BP" + k + "+LR" + k), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Bad pedestal and very noisy",
                                                                          GHC.getNumChannelsWithFlag(
                                                                              ["BP" + k, "VLR" + k],
                                                                              det=d),
                                                                          "BP" + k + "+VLR" + k), file=log_textile)
        print("", file=log_textile)

        tpc = 0
        print("|=. Statistics by FLAGS", file=log_textile)
        print("|_. Flag |_. Number of channels |", file=log_textile)
        for k in ["G1", "G6", "G12"]:
            for i in GHC.PEDESTAL_FLAGS:
                num = GHC.getNumChannelsWithFlag(i + k, det=d)
                tpc += num
                print("| {0:8s} | {1:5d} |".format(i + k, num), file=log_textile)
        print("", file=log_textile)

        # Images
        print(header("Plots", 3), file=log_textile)
        print("", file=log_textile)
        print("table(imgtab).", file=log_textile)
        lines = ([], [], [], [], [], [], [], [])
        for k in ["G1", "G6", "G12"]:
            lines[0].append(mkImgLink("pedestals_hvon/{0}_MEAN_{1}.1D.{2}".format(k, d, ext)))
            lines[1].append("Pedestal mean value distribution (HV ON, gain {0})".format(k[1:]))
            lines[2].append(mkImgLink("pedestals_hvon/{0}_RMS_{1}.1D.{2}".format(k, d, ext)))
            lines[3].append("Pedestal rms distribution (HV ON, gain {0})".format(k[1:]))

            lines[4].append(mkImgLink("pedestals_hvoff/{0}_MEAN_{1}.1D.{2}".format(k, d, ext)))
            lines[5].append("Pedestal mean value distribution (HV OFF, gain {0})".format(k[1:]))
            lines[6].append(mkImgLink("pedestals_hvoff/{0}_RMS_{1}.1D.{2}".format(k, d, ext)))
            lines[7].append("Pedestal rms distribution (HV OFF, gain {0})".format(k[1:]))

        print_lines()
        print("", file=log_textile)

    print(header("Pedestal maps", 2), file=log_textile)
    print("", file=log_textile)
    print("table(imgtab).", file=log_textile)
    lines = ([], [], [], [], [], [], [], [])
    for k in ["G1", "G6", "G12"]:
        lines[0].append(mkImgLink("pedestals_hvon/{0}_MEAN.2D.{1}".format(k, ext)))
        lines[1].append("Pedestal mean value map (HV ON, gain {0})".format(k[1:]))
        lines[2].append(mkImgLink("pedestals_hvon/{0}_RMS.2D.{1}".format(k, ext)))
        lines[3].append("Pedestal rms map (HV ON, gain {0})".format(k[1:]))

        lines[4].append(mkImgLink("pedestals_hvoff/{0}_MEAN.2D.{1}".format(k, ext)))
        lines[5].append("Pedestal mean value map (HV OFF, gain {0})".format(k[1:]))
        lines[6].append(mkImgLink("pedestals_hvoff/{0}_RMS.2D.{1}".format(k, ext)))
        lines[7].append("Pedestal rms map (HV OFF, gain {0})".format(k[1:]))

    print_lines()
else:
    print("No pedestal data present!", file=log_textile)

print("", file=log_textile)
print(header("TEST PULSE ANALYSIS"), file=log_textile)
if GHC.has_testpulse:
    for d in ("EB", "EE"):
        print(header("TEST PULSE {0} ANALYSIS".format(d), 2), file=log_textile)
        print("", file=log_textile)
        print("|=. Channel statistics ({0})".format(d), file=log_textile)
        print("|_. &nbsp; |_. Gain 1 |_. Gain 6 |_. Gain 12 |", file=log_textile)
        lines = (["Missing channels"], ["Active channels"])

        for g in ("G1", "G6", "G12"):
            act = GHC.getNumOfActiveChannels(d, 'ADC_MEAN_' + g)
            lines[0].append("{0}".format((61200, 14648)[d == "EE"] - act))
            lines[1].append("{0}".format(act))

        print_lines(150, 180)
        print("", file=log_textile)

        print("|=. Classes of Test Pulse problematic channels", file=log_textile)
        print("|_. {classn:41s} |_. {empty:3s} |_. {tags:21s} |".format(
            classn="&nbsp;",
            empty="Count", tags="Short name"), file=log_textile)

        for k in ("G1", "G6", "G12"):
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Dead TP channels",
                                                                          GHC.getNumChannelsWithFlag("DTP" + k, det=d),
                                                                          "DTP" + k), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Low TP amplitude",
                                                                          GHC.getNumChannelsWithFlag("STP" + k, det=d),
                                                                          "STP" + k), file=log_textile)
            print("| {0:43s} | {1:5d} | {2:23s} |".format("Large TP amplitude",
                                                                          GHC.getNumChannelsWithFlag("LTP" + k, det=d),
                                                                          "LTP" + k), file=log_textile)
        print("", file=log_textile)

        print("|=. Statistics by FLAGS", file=log_textile)
        print("|_. Flag |_. Number of channels |", file=log_textile)
        for k in ("G1", "G6", "G12"):
            for i in GHC.TESTPULSE_FLAGS:
                num = GHC.getNumChannelsWithFlag(i + k, det=d)
                print("| {0:8s} | {1:5d} |".format(i + k, num), file=log_textile)
        print("", file=log_textile)

        # Images
        print(header("Plots", 3), file=log_textile)
        print("", file=log_textile)
        print("table(imgtab).", file=log_textile)
        lines = ([], [], [], [])
        for k in ["G1", "G6", "G12"]:
            lines[0].append(mkImgLink("testpulse/{0}_MEAN_{1}.1D.{2}".format(k, d, ext)))
            lines[1].append("Test pulse mean value distribution (gain {0})".format(k[1:]))
            lines[2].append(mkImgLink("testpulse/{0}_RMS_{1}.1D.{2}".format(k, d, ext)))
            lines[3].append("Test pulse rms distribution (gain {0})".format(k[1:]))

        print_lines()
        print("", file=log_textile)

    print(header("Test pulse maps", 2), file=log_textile)
    print("", file=log_textile)
    print("table(imgtab).", file=log_textile)
    lines = ([], [], [], [])
    for k in ["G1", "G6", "G12"]:
        lines[0].append(mkImgLink("testpulse/{0}_MEAN.2D.{1}".format(k, ext)))
        lines[1].append("Test pulse mean value map (gain {0})".format(k[1:]))
        lines[2].append(mkImgLink("testpulse/{0}_RMS.2D.{1}".format(k, ext)))
        lines[3].append("Test pulse rms map (gain {0})".format(k[1:]))

    print_lines()
else:
    print("No testpulse data present", file=log_textile)

print("", file=log_textile)
print(header("LASER ANALYSIS"), file=log_textile)
if GHC.has_laser:
    for d in ("EB", "EE"):
        print("", file=log_textile)
        print(header("LASER {0} ANALYSIS".format(d), 2), file=log_textile)
        print("", file=log_textile)

        print("|=. Channel statistics ({0})".format(d), file=log_textile)
        print("|_. &nbsp; |_. Gain 1 |_. Gain 6 |_. Gain 12 |", file=log_textile)
        lines = (["Missing channels"], ["Active  channels"])

        for g in ("G1", "G6", "G12"):
            act = GHC.getNumOfActiveChannels(d, 'APD_MEAN')
            lines[0].append("{0}".format((61200, 14648)[d == "EE"] - act))
            lines[1].append("{0}".format(act))

        print_lines(150, 180)
        print("", file=log_textile)

        print("|=. Statistic by FLAG", file=log_textile)
        print("|_. Flag |_. Number of channels |", file=log_textile)
        for i in GHC.LASER_FLAGS:
            print("| {0:15s} | {1:5d} |".format(i, GHC.getNumChannelsWithFlag(i, det=d)), file=log_textile)

        print("", file=log_textile)
        # Images
        print(header("Plots", 3), file=log_textile)
        print("", file=log_textile)
        print("table(imgtab).", file=log_textile)
        lines = ([mkImgLink("laser/{0}_MEAN_{1}.1D.{2}".format("LASER", d, ext)),
                  mkImgLink("laser/{0}_RMS_{1}.1D.{2}".format("LASER", d, ext))],
                 ["Laser amplitude mean value distribution",
                  "Laser amlitude rms distribution"],
                 [mkImgLink("laser/{0}_MEAN_{1}.1D.{2}".format("APDPN", d, ext)),
                  mkImgLink("laser/{0}_RMS_{1}.1D.{2}".format("APDPN", d, ext))],
                 ["APD/PN mean value distribution",
                  "APD/PN rms distribution"]
                 )

        print_lines()
        print("", file=log_textile)

    print(header("Laser maps", 2), file=log_textile)
    print("", file=log_textile)
    print("table(imgtab).", file=log_textile)

    lines = ([mkImgLink("laser/{0}_MEAN.2D.{1}".format("Laser", ext)),
              mkImgLink("laser/{0}_RMS.2D.{1}".format("Laser", ext))],
             ["Laser amplitude mean value map",
              "Laser amlitude rms map"],
             [mkImgLink("laser/{0}_MEAN.2D.{1}".format("APDPN", ext)),
              mkImgLink("laser/{0}_RMS.2D.{1}".format("APDPN", ext))],
             ["APD/PN mean value map",
              "APD/PN rms map"]
             )

    print_lines()
    print("", file=log_textile)
else:
    print("No laser data present", file=log_textile)

# Summary tables

# logger.setLevel(logging.DEBUG)

prob_dict = OrderedDict([('Pedestals problems', [GHC.PEDESTAL_FLAGS, GHC.has_ped_hvon, 'PE']),
                         ('Test Pulse problems', [GHC.TESTPULSE_FLAGS, GHC.has_testpulse, 'TP']),
                         ('Laser problems', [GHC.LASER_FLAGS, GHC.has_laser, 'LA']),
                         ('High voltage problems', [GHC.HV_FLAGS, GHC.has_ped_hvoff, 'HV'])])

for d in ("EB", "EE"):
    for k, v in prob_dict.items():
        if v[2] == 'HV' and d != 'EE':
            v.append(set())
            continue

        v.append(set(GHC.getChannelsWithFlag([x + '%' for x in v[0]], exp='or', det=d)))

prob_keys = [(x,) for x in list(prob_dict.keys())]
prob_keys.extend(itertools.combinations(list(prob_dict.keys()), 2))
prob_keys.extend(itertools.combinations(list(prob_dict.keys()), 3))
prob_keys.extend(itertools.combinations(list(prob_dict.keys()), 4))

# logger.debug("prob_keys: %s", str(prob_keys))

headers = [[("Problem classes (\"at least\")", 2), ("Number of channels", 1)]]

for d in ("EB", "EE"):
    body = []

    print("", file=log_textile)
    print(header("Problematic Channels Summary for {0}".format(d)), file=log_textile)
    print("", file=log_textile)

    for key in prob_keys:
        # logger.debug("key: %s", str(key))
        body1 = ' + '.join(key)
        body2 = '+'.join(prob_dict[x][2] for x in key)
        cond = all(prob_dict[x][1] for x in key)

        # logger.debug("body1: %s", body1)
        # logger.debug("body2: %s", body2)
        # logger.debug("flags: %s", flags)

        if 'HV' in body2 and d != 'EE':
            continue

        if not cond:
            data = "No Data" if len(key) == 1 else "Not Enough Data"
        else:
            # data = GHC.getNumChannelsWithFlag(flags, exp='and', det=d)
            if len(key) == 1:
                # logger.debug("channels: %s", prob_dict[key[0]][3])
                data = len(prob_dict[key[0]][3])
            else:
                data = copy.copy(prob_dict[key[0]][3])
                # logger.debug("channels: %s", prob_dict[key[0]][3])
                for x in key:
                    data &= prob_dict[x][3]
                    # logger.debug("channels: add %s, now %s", prob_dict[x][3], data)

                data = len(data)

        body.append((body1, body2, str(data)))

    print(textile.fancy_table(headers, body), file=log_textile)
    print("", file=log_textile)

# logger.setLevel(logging.INFO)
if args.verbose:
    logging.info("Creating summary table")
    log_flags = open(os.path.join(outputdir, 'flags.textile'), 'w')
    GHC.printProblematicChannelsTable(log_flags)
    log_flags.close()
    logging.info("Converting summary table")
    textile2html.convert(os.path.join(outputdir, 'flags.textile'))

# if args.verbose: or args.expert:
    print("p. \"Summary of all channels with flags\":flags.html\n", file=log_textile)
if args.csv:
    logging.info("Creating CSV file")
    with open("ghc_{0}_r.csv".format(args.ghc_id), "w") as f:
        GHC.printProblematicChannelsCSV(f)

if not args.noplots:
    # plotting
    plotter = Plotter(GHC)
    logging.info("Creating plots")

    for subdir in ['pedestals_hvon', 'pedestals_hvoff', 'testpulse', 'laser']:
        if not os.path.exists(outputdir + "/" + subdir):
            os.mkdir(outputdir + "/" + subdir)

    for plottype in ('MEAN', 'RMS'):
        for g in ("G1", "G6", "G12"):
            for d in ("EB", "EE"):
                ### 1D plots
                h = plotter.get1DHistogram(key=("PED_ON_{0}_{1}".format(plottype, g)).upper(), det=d,
                                           name="Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV ON"))
                plotter.saveHistogram(h, outputdir + "/pedestals_hvon/{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(),
                                                                                                 d, ext))

                h = plotter.get1DHistogram(key=("PED_OFF_{0}_{1}".format(plottype, g)).upper(), det=d,
                                           name="Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV OFF"))
                plotter.saveHistogram(h, outputdir + "/pedestals_hvoff/{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(),
                                                                                                  d, ext))

                h = plotter.get1DHistogram(key=("ADC_{0}_{1}".format(plottype, g)).upper(), det=d,
                                           name="Test Pulse {0}, gain {1}".format(plottype, g))
                plotter.saveHistogram(h,
                                      outputdir + "/testpulse/{0}_{1}_{2}.1D.{3}".format(g, plottype.upper(), d, ext))

            ### 2D plots
            h = plotter.get2DHistogram(key=("PED_ON_{0}_{1}".format(plottype, g)).upper(),
                                       name="Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV ON"))
            plotter.saveHistogram(h, outputdir + "/pedestals_hvon/{0}_{1}.2D.{2}".format(g, plottype.upper(), ext))

            h = plotter.get2DHistogram(key=("PED_OFF_{0}_{1}".format(plottype, g)).upper(),
                                       name="Pedestal {0}, gain {1} ({2})".format(plottype, g, "HV OFF"))
            plotter.saveHistogram(h, outputdir + "/pedestals_hvoff/{0}_{1}.2D.{2}".format(g, plottype.upper(), ext))

            h = plotter.get2DHistogram(key="ADC_{0}_{1}".format(plottype.upper(), g),
                                       name="Test Pulse {0}, gain {1}".format(plottype, g))
            plotter.saveHistogram(h, outputdir + "/testpulse/{0}_{1}.2D.{2}".format(g, plottype.upper(), ext))

        for d in ("EB", "EE"):
            ### laser plots
            h = plotter.get1DHistogram(key=("APD_{0}".format(plottype)).upper(), det=d,
                                       name="Laser {0} ({1})".format(plottype, args.lasertable))
            plotter.saveHistogram(h, outputdir + "/laser/Laser_{0}_{1}.1D.{2}".format(plottype.upper(), d, ext))

            h = plotter.get1DHistogram(key="APD_OVER_PN_{0}".format(plottype), det=d,
                                       name="APD/PN {0} ({1})".format(plottype, args.lasertable))
            plotter.saveHistogram(h, outputdir + "/laser/APDPN_{0}_{1}.1D.{2}".format(plottype.upper(), d, ext))

        ### 2D laser plots
        h = plotter.get2DHistogram(key="APD_{0}".format(plottype.upper()),
                                   name="Laser {0} ({1})".format(plottype, args.lasertable))
        plotter.saveHistogram(h, outputdir + "/laser/Laser_{0}.2D.{1}".format(plottype.upper(), ext))

        h = plotter.get2DHistogram(key="APD_OVER_PN_{0}".format(plottype.upper()),
                                   name="APD/PN {0} ({1})".format(plottype, args.lasertable))
        plotter.saveHistogram(h, outputdir + "/laser/APDPN_{0}.2D.{1}".format(plottype.upper(), ext))

# description of error types
print(header("Description of errors"), file=log_textile)

print("""h2. Description of errors for EB

Dead pedestal  (DP)

* Gain 1 : MEAN <= 1 or RMS <= 0.2
* Gain 6 : MEAN <= 1 or RMS <= 0.4
* Gain 12: MEAN <= 1 or RMS <= 0.5

 Bad pedestal   (BP)

* abs(MEAN - 200) >= 30 and MEAN > 1

 Large RMS      (LR)

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS >= 1.1 and RMS < 3 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS >= 1.3 and RMS < 4 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS >= 2.1 and RMS < 6 and MEAN > 1)

 Very Large RMS (VLR)

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS > 3 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS > 4 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS > 6 and MEAN > 1)

h2. Description of errors for EE

 Dead pedestal  (DP)

* Gain 1 : MEAN <= 1 or RMS <= 0.2
* Gain 6 : MEAN <= 1 or RMS <= 0.4
* Gain 12: MEAN <= 1 or RMS <= 0.5

 Bad pedestal   (BP)

* abs(MEAN - 200) >= 30 and MEAN > 1

 Large RMS      (LR)

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS >= 1.5 and RMS < 4 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS >= 2.0 and RMS < 5 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS >= 3.2 and RMS < 7 and MEAN > 1)

 Very Large RMS (VLR)

* Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS > 4 and MEAN > 1)
* Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS > 5 and MEAN > 1)
* Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS > 7 and MEAN > 1)

h2. Description of HV OFF errors:

 Bad Voltage for G12 (BV)

* abs(RMS&#40;HVON) - RMS&#40;HVOFF)) < 0.2 and 170 <= MEAN&#40;HVON) <= 230

h2. Description of Test Pulse errors

 Dead TestPulse          (DTP)

* MEAN = 0

 Low TestPulse amplitude (STP)

* AVG = average mean for each subdetector (EB, EE)
* MEAN > 0 and MEAN < 0.5 * AVG

 Large TP amplitude      (LTP)

* MEAN > 1.5 * AVG

h2. Description of Laser Pulse errors:

* DLAMPL: MEAN <= 0
* SLAMPL: MEAN > 0 and MEAN < AVG * 0.1         # AVG per subdetector
* LLERRO: MEAN > AVG * 0.1 and RMS / MEAN > 0.1 # AVG per subdetector
""", file=log_textile)

endts = datetime.datetime.now()
print("\np. Elapsed time:", str(endts - startts), file=log_textile)

log_textile.close()

logging.info("Producing HTML file")
textile2html.convert(os.path.join(outputdir, 'index.textile'), notoc=False)
logging.info("Done")
