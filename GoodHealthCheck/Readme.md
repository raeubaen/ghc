Good Health Check
=================

This documentation is prepared for Good Health Check (GHC) utilities. It can be used for
solving problems with channels in CMS ECAL detector.

Good Health Check structure
---------------------------
GHC is written in Python and has modular structure. The **modules** directory has Python GHC modules that is used by Python GHC scripts. At the moment the following modules are available:

  * Data.py
  * connection.py
  * laser-proc/
  * thresholds.py

These modules are used by GHC python scripts which do analysis and make plots. The following scripts are available:

  * ghc.py
  * compare.py
  * Plot.py

Also there are some additional files that helps to use GHC:

  * setup.sh
  * Settings.py
  * VALUEKEYS.txt
  * textile2html.py
  * clear_ghc_data.py

Modules
-------

To get more info about inner structure of modules run `PYTHONPATH=modules pydoc modules/*.py`

### Data.py  

The *Data.py* module provides basic data structure and functions for all scripts.

### log.py ###

This modules print INFO or DEBUG messages and raise RuntimeError if it is needed.

Scripts
-------

Each script has command line option parser, so -h option will give you some useful information.

### ghc.py ###

This is main script which uses Data module and provide userful output.

<pre>
usage: ghc.py [-h] [-c DBSTR] [-pon PON_RUNS] [-poff POFF_RUNS] [-tp TP_RUNS]
              [-l L_RUNS] [-o DIRECTORY] [-f FORMAT] [-r] [--csv] [-k] [-q] 
              [-np] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  -c DBSTR, --dbstr DBSTR
                        Connection string to DB (oracle://user/pass@db). Don't
                        use this if you want to read files.
  -pon PON_RUNS         Pedestal HV ON runs numbers or list of files
  -poff POFF_RUNS       Pedestal HV OFF runs numbers or list of files
  -tp TP_RUNS           Test Pulse runs numbers or list of files
  -l L_RUNS             Laser runs or list of files
  -o DIRECTORY, --output DIRECTORY
                        Results directory
  -f FORMAT, --format FORMAT
                        Results format (defaults to png and root)
  -r, --redo            Redo existing GHC. Specify twice to re-classify channels
  --csv                 Create csv file with a list of problematic channels
  -q, --quiet           Don't print summary table with problematic channels
  -np, --no-plots       Don't make plots
  --debug               Enable more verbose logging

</pre>
 
The following rules are used for assign some flags to channels:

How to use
==========

** Setup ** 
  source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh

  cd pfgutils
  pip install -e .

  ssh -o ExitOnForwardFailure=yes -f -N -L 10121:cmsonr1-v.cern.ch:10121 USERNAME@cmsusr.cern.ch 

**Example of analyse GHC1**
    cd GoodHealthCheck
    python ghc.py -h
    python ghc.py --csv -o "results" -pon "392414" -poff "390112" -tp "392424" -l "392430" 1 |& tee ghc.log
    python clear_ghc_data.py -s 1 -e 1

You should see various output about channels in the results folder
