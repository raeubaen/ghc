#!/usr/bin/env python
import argparse
import copy
import csv

from ghc_modules import Data

footer = """<pre>
Description of errors for EB
  Dead pedestal  (DP)  :
    Gain 1 : MEAN <= 1 or RMS <= 0.2
    Gain 6 : MEAN <= 1 or RMS <= 0.4
    Gain 12: MEAN <= 1 or RMS <= 0.5
  Bad pedestal   (BP)  :
    abs(MEAN - 200) >= 30 and MEAN > 1
  Large RMS      (LR)  :
    Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS >= 1.1 and RMS < 3 and MEAN > 1)
    Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS >= 1.3 and RMS < 4 and MEAN > 1)
    Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS >= 2.1 and RMS < 6 and MEAN > 1)
  Very Large RMS (VLR) :
    Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS > 3 and MEAN > 1)
    Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS > 4 and MEAN > 1)
    Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS > 6 and MEAN > 1)

Description of errors for EE
  Dead pedestal  (DP)  :
    Gain 1 : MEAN <= 1 or RMS <= 0.2
    Gain 6 : MEAN <= 1 or RMS <= 0.4
    Gain 12: MEAN <= 1 or RMS <= 0.5
  Bad pedestal   (BP)  :
    abs(MEAN - 200) >= 30 and MEAN > 1
  Large RMS      (LR)  :
    Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS >= 1.5 and RMS < 4 and MEAN > 1)
    Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS >= 2.0 and RMS < 5 and MEAN > 1)
    Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS >= 3.2 and RMS < 7 and MEAN > 1)
  Very Large RMS (VLR) :
    Gain 1 : (not (MEAN <= 1 or RMS <= 0.2)) and (RMS > 4 and MEAN > 1)
    Gain 6 : (not (MEAN <= 1 or RMS <= 0.4)) and (RMS > 5 and MEAN > 1)
    Gain 12: (not (MEAN <= 1 or RMS <= 0.5)) and (RMS > 7 and MEAN > 1)

Description of HV OFF errors:
  Bad Voltage for G12 (BV):
    abs(MEAN&#40;HVON) - MEAN&#40;HVOFF)) < 0.2 and 170 <= MEAN&#40;HVON) <= 230

Description of Test Pulse errors
  Dead TestPulse          (DTP):
    MEAN = 0
  Low TestPulse amplitude (STP):
    AVG = average mean for each subdetector (EB, EE)
    MEAN > 0 and MEAN < 0.5 * AVG
  Large TP amplitude      (LTP):
    MEAN > 1.5 * AVG

Description of Laser Pulse errors:
  DLAMPL: MEAN <= 0
  SLAMPL: MEAN > 0 and MEAN < AVG * 0.1         # AVG per subdetector
  LLERRO: MEAN > AVG * 0.1 and RMS / MEAN > 0.1 # AVG per subdetector
</pre>"""


def decode_flag(flag):
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


def format_flag(bad_channel, flag):
    global GHC
    res = decode_flag(flag)
    if flag.startswith('DP') or flag.startswith('BP') or flag.startswith('LR') or flag.startswith('VLR'):
        # Pedestal error
        gain = 'G' + flag.split('G', 1)[1]
        mean = float(GHC.getChannelData(bad_channel, key='PED_ON_MEAN_{0}'.format(gain)))
        rms = float(GHC.getChannelData(bad_channel, key='PED_ON_RMS_{0}'.format(gain)))
        res += ' ({0:.2f} &#177; {1:.2f})'.format(mean, rms)

    if flag.startswith('DTP') or flag.startswith('STP') or flag.startswith('LTP'):
        gain = 'G' + flag.split('G', 1)[1]
        mean = float(GHC.getChannelData(bad_channel, key='ADC_MEAN_{0}'.format(gain)))
        rms = float(GHC.getChannelData(bad_channel, key='ADC_RMS_{0}'.format(gain)))
        res += ' ({0:.2f} &#177; {1:.2f})'.format(mean, rms)

    if flag.startswith('BV'):
        gain = 'G' + flag.split('G', 1)[1]
        mean_on = float(GHC.getChannelData(bad_channel, key='PED_ON_RMS_{0}'.format(gain)))
        mean_off = float(GHC.getChannelData(bad_channel, key='PED_OFF_RMS_{0}'.format(gain)))
        res += ' (ON: {0:.2f}, OFF: {1:.2f})'.format(mean_on, mean_off)

    if flag in ('DLAMPL', 'SLAMPL', 'LLERRO'):
        mean = float(GHC.getChannelData(bad_channel, key='APD_MEAN'))
        rms = float(GHC.getChannelData(bad_channel, key='APD_RMS'))
        res += ' ({0:.2f} &#177; {1:.2f})'.format(mean, rms)

    return res


def main():
    global GHC

    parser = argparse.ArgumentParser()
    parser.add_argument('ghc_id', help='GHC id to validate', metavar='ghc')
    parser.add_argument('-m', '--master', help="File to use as master (default: ghc_<id>.csv)", dest='master',
                        default='/afs/cern.ch/user/r/razumov/public/GHC_test/ghc_{0}.csv')
    parser.add_argument('-r', '--rewrite', help="File to use as rewrite(default: ghc_<id>_r.csv", dest='rewrite',
                        default='ghc_{0}_r.csv')
    parser.add_argument('-o', '--output', help="Output file name", dest='out', default='validate.textile')
    parser.add_argument('-d', '--delim', help="Delimiter of fields in input files", dest='delim', default='|')

    args = parser.parse_args()

    GHC = Data.Data(args.ghc_id)

    master = {}
    rewrite = {}

    master_name = args.master.format(args.ghc_id)

    print("Reading file produced from master branch:", master_name)
    with open(master_name, 'r') as f:
        reader = csv.reader(f, delimiter=args.delim)
        for row in reader:
            channel = row[0].strip()
            if channel.startswith('1') or channel.startswith('2'):
                master[int(channel)] = set(sorted(row[1].strip().split('+')))

    print("Done, found %d channels" % len(master))

    rewrite_name = args.rewrite.format(args.ghc_id)
    print("Reading file produced by rewrite branch:", rewrite_name)
    with open(rewrite_name, 'r') as f:
        reader = csv.reader(f, delimiter=args.delim)
        for row in reader:
            channel = row[0].strip()
            if channel.startswith('1') or channel.startswith('2'):
                rewrite[int(channel)] = set(sorted(row[1].strip().split('+')))

    print("Done, found %d channels" % len(rewrite))

    print("Comparing results")

    m_keys = set(master.keys())
    r_keys = set(rewrite.keys())

    print("* Number of channels present only in one file: %d" % len(m_keys ^ r_keys))

    outfile = open(args.out, "w")
    outfile.write("table.\n")
    outfile.write("|=. Channel flags validation\n")
    outfile.write("|_. Channel |_. Flags (common) |_. Flags (only master) |_. Flags (only rewrite) |\n")

    for channel_id in sorted(m_keys | r_keys):
        try:
            master_flags = master[channel_id]
        except (KeyError, IndexError):
            master_flags = set()

        try:
            rewrite_flags = rewrite[channel_id]
        except (KeyError, IndexError):
            rewrite_flags = set()

        m = copy.copy(master_flags)
        r = copy.copy(rewrite_flags)

        master_flags = master_flags - r
        rewrite_flags = rewrite_flags - m

        common_text = ", ".join(m.intersection(r))
        master_text = ", ".join(format_flag(channel_id, x) for x in master_flags)
        rewrite_text = ", ".join(format_flag(channel_id, x) for x in rewrite_flags)

        outfile.write("| %d | %s | %s | %s |\n" % (channel_id, common_text, master_text, rewrite_text))

    outfile.write("\n")
    outfile.write(footer)
    outfile.close()
    import textile2html

    textile2html.convert(args.out)


if __name__ == '__main__':
    GHC = None
    main()
