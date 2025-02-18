#!/bin/bash

curdir="$(python -c "import sys, os; print os.path.realpath(os.path.dirname(\"$0\"))")"

for i in */bin; do
  export PATH=$curdir/$i:$PATH
done

for i in */lib; do
  export LD_LIBRARY_PATH=$curdir/$i:$LD_LIBRARY_PATH
  export LIBRARY_PATH=$curdir/$i:$LIBRARY_PATH
done

for i in */include; do
  export C_INCLUDE_PATH=$curdir/$i:$C_INCLUDE_PATH
  export CPLUS_INCLUDE_PATH=$curdir/$i:$CPLUS_INCLUDE_PATH
done
export PYTHONPATH=$curdir/psycopg2:$PYTHONPATH
