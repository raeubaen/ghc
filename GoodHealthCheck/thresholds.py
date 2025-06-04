CONFIG = {

# EB
##############################################################################

  "EB": {
    # MEAN <= {0} or RMS <= {1} 
    "DP": {
      "G1": [1, 0.2],
      "G6": [1, 0.4],
      "G12": [1, 0.5]
    },
    
    # abs(MEAN - {0}) >= {1} and MEAN > {2}
    "BP": [220, 50, 1],

    # (not (DP) and (RMS >= {0} and RMS < {1} and MEAN > {2})
    "LR": {
      "G1": [5, 10, 1],
      "G6": [5, 10, 1],
      "G12": [5, 10, 1]
    },

    # (not (DP) and (RMS > {0} and MEAN > {1})
    "VLR": {
      "G1": [10, 1],
      "G6": [10, 1],
      "G12": [10, 1]
    },
    # abs(RMS&#40;HVON) - RMS&#40;HVOFF)) < {0} and {1} <= MEAN&#40;HVON) <= {2}
    "BV": [0.2, 170, 270],

    # MEAN = {0}
    "DTP": [0],

    # AVG = average mean for each subdetector (EB, EE)
    # MEAN > {0} and MEAN < {1} * AVG
    "STP": [0, 0.5],

    # MEAN > {0} * AVG
    "LTP": [1.5],

    # MEAN <= {0}
    "DLAMPL": [5],
 
    # MEAN > {0} and MEAN < AVG * {1}         # AVG per subdetector
    "SLAMPL": [0, 0.1],

    # LLERRO: MEAN > AVG * {0} and RMS / MEAN > {1} # AVG per subdetector
    "LLERRO": [0.1, 0.1],

    # DLAMPL_OVERPN: MEAN_OVER_PN <= {0}
    "DLAMPL_OVERPN": [0.2],

    # SLAMPL_OVERPN: MEAN_OVER_PN > {0} and MEAN_OVER_PN < AVG * {1}         # AVG per subdetector
    "SLAMPL_OVERPN": [0, 0.1]
  },

# EE
##############################################################################
 
  "EE": {
    # MEAN <= {0} or RMS <= {1}
    "DP": {
      "G1": [1, 0.2],
      "G6": [1, 0.4],
      "G12": [1, 0.5]
    },

    # abs(MEAN - {0}) >= {1} and MEAN > {2}
    "BP": [260, 90, 1],

    # (not (DP) and (RMS >= {0} and RMS < {1} and MEAN > {2})
    "LR": {
      "G1": [5, 10, 1],
      "G6": [5, 10, 1],
      "G12": [5, 10, 1]
    },

    # (not (DP) and (RMS > {0} and MEAN > {1})
    "VLR": {
      "G1": [10, 1],
      "G6": [10, 1],
      "G12": [10, 1]
    },

    # abs(RMS&#40;HVON) - RMS&#40;HVOFF)) < {0} and {1} <= MEAN&#40;HVON) <= {2}
    "BV": [0.2, 170, 350],

    # MEAN = {0}
    "DTP": [0],

    # AVG = average mean for each subdetector (EB, EE)
    # MEAN > {0} and MEAN < {1} * AVG
    "STP": [0, 0.5],

    # MEAN > {0} * AVG
    "LTP": [1.5],

    # MEAN <= {0} 
    "DLAMPL": [5],
 
    # MEAN > {0} and MEAN < AVG * {1}         # AVG per subdetector 
    "SLAMPL": [0, 0.005],

    # LLERRO: MEAN > AVG * {0} and RMS / MEAN > {1} # AVG per subdetector
    "LLERRO": [0.1, 0.1],

    # DLAMPL_OVERPN: MEAN_OVER_PN <= {0}
    "DLAMPL_OVERPN": [0.001],

    # SLAMPL_OVERPN: MEAN_OVER_PN > {0} and MEAN_OVER_PN < AVG * {1}         # AVG per subdetector
    "SLAMPL_OVERPN": [0, 0.0005]
  }
}

