import pandas as pd
import numpy as np
import ROOT

from Plugin import Plugin



FEstatus_labels = ["ENABLED", "DISABLED", "TIMEOUT", "HEADERERROR", "CHANNELID", "LINKERROR", "BLOCKSIZE", "SUPPRESSED","FORCEDFULLSUPP",
"L1ADESYNC", "BXDESYNC", "L1ABXDESYNC", "FIFOFULL", "HPARITY", "VPARITY", "FORCEDZS"]


EBsupermodules_list = ["EB-18", "EB-17", "EB-16", "EB-15", "EB-14", "EB-13", "EB-12", "EB-11", "EB-10", "EB-09", "EB-08",
"EB-07", "EB-06", "EB-05", "EB-04", "EB-03", "EB-02", "EB-01", "EB+01", "EB+02", "EB+03", "EB+04", "EB+05", "EB+06", "EB+07",
"EB+08", "EB+09", "EB+10", "EB+11", "EB+12", "EB+13", "EB+14", "EB+15", "EB+16", "EB+17", "EB+18"]


EEsupermodules_list = ["EE-09", "EE-08", "EE-07", "EE-06", "EE-05", "EE-04", "EE-03", "EE-02", "EE-01", "EE+01", "EE+02", "EE+03",
"EE+04", "EE+05", "EE+06", "EE+07", "EE+08", "EE+09"]


supermodules_FED_match = {"EB-18": 627, "EB-17": 626, "EB-16": 625, "EB-15": 624, "EB-14": 623, "EB-13": 622, "EB-12": 621, "EB-11": 620,
"EB-10": 619, "EB-09": 618, "EB-08": 617, "EB-07": 616, "EB-06": 615, "EB-05": 614, "EB-04": 613, "EB-03": 612, "EB-02": 611,
"EB-01": 610, "EB+01": 628, "EB+02": 629, "EB+03": 630, "EB+04": 631, "EB+05": 632, "EB+06": 633, "EB+07": 634, "EB+08": 635,
"EB+09": 636, "EB+10": 637, "EB+11": 638, "EB+12": 639, "EB+13": 640, "EB+14": 641, "EB+15": 642, "EB+16": 643, "EB+17": 644,
"EB+18": 645, "EE-09": 603, "EE-08": 602, "EE-07": 601, "EE-06": 609, "EE-05": 608, "EE-04": 607, "EE-03": 606, "EE-02": 605,
"EE-01": 604, "EE+01": 649, "EE+02": 650, "EE+03": 651, "EE+04": 652, "EE+05": 653, "EE+06": 654, "EE+07": 646, "EE+08": 647, "EE+09": 648}


FEstatus_match = {"ENABLED": 1, "DISABLED": 2, "TIMEOUT": 3, "HEADERERROR": 4, "CHANNELID": 5, "LINKERROR": 6, "BLOCKSIZE": 7, "SUPPRESSED": 8,"FORCEDFULLSUPP": 9,
"L1ADESYNC": 10, "BXDESYNC": 11, "L1ABXDESYNC": 12, "FIFOFULL": 13, "HPARITY": 14, "VPARITY": 15, "FORCEDZS": 16}


EELightMonitoringRegions = np.array([[0, 0, 0, 0, 0, 0, 0, 18, 18, 18],
    [0, 0, 0, 0, 16, 16, 16, 18, 18, 18],
    [0, 0, 0, 15, 15, 15, 16, 18, 18, 18],
    [0, 0, 14, 15, 15, 15, 16, 16, 19, 19],
    [0, 14, 14, 14, 14, 15, 16, 16, 19, 19],
    [0, 12, 14, 14, 14, 15, 16, 17, 19, 19],
    [0, 12, 13, 13, 14, 15, 17, 17, 17, 19],
    [12, 12, 13, 13, 13, 11, 17, 17, 17, 19],
    [12, 12, 13, 10, 10, 11, 11, 17, 17, 0],
    [12, 9, 9, 10, 10, 11, 11, 11, 0, 0],
    [9, 9, 9, 10, 10, 11, 11, 7, 0, 0],
    [9, 9, 8, 6, 6, 7, 7, 7, 7, 0],
    [8, 8, 8, 6, 6, 7, 7, 7, 4, 4],
    [0, 8, 8, 5, 6, 6, 7, 4, 4, 4],
    [0, 8, 8, 5, 6, 6, 4, 4, 4, 3],
    [0, 8, 5, 5, 5, 3, 3, 3, 3, 3],
    [0, 0, 5, 5, 5, 3, 3, 2, 2, 2],
    [0, 0, 0, 5, 2, 2, 2, 2, 2, 1],
    [0, 0, 0, 0, 2, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1]])


#from coordinates (eta, phi for the barrel or x, y for the endcaps) to SM, tcc, tt/ccu
def fill_tcc_tt(df_xphi_yeta, supermodules_FED, ccu=False):
        SM_label = next((key for key, fe in supermodules_FED.items() if fe == df_xphi_yeta["fed"].iloc[0]), None)
        tt = df_xphi_yeta["tower"].iloc[0]
        if ccu == True:
                tt = df_xphi_yeta["ccu"].iloc[0]
        tcc = df_xphi_yeta["tcc"].iloc[0]
        return {"SM_label": SM_label, "tt_ccu": tt, "tcc": tcc}


def EELightMR(x, y):
    if (x < 0 or x > 100):
        return 0
    if (y < 0 or y > 100):
        return 0
    xtt = x - 1
    if (x > 50):
        xtt = 50 - abs(x - 50)
    xtt = int(xtt / 5)
    ytt = int((y - 1) / 5)
    region = EELightMonitoringRegions[ytt][xtt]
    return region
