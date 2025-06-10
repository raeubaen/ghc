#!/usr/bin/env bash

set -eo pipefail

if [ -f "/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh" ]; then
  . "/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh"
else
  echo "Error: could not find setup.sh" >&2
  exit 1
fi

# . "$HOME/lcg-example/bin/activate"

cd "$HOME/ghc/GoodHealthCheck"


python3 ghc.py "$@"
