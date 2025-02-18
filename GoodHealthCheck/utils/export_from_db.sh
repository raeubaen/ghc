#!/bin/sh

usage(){
  echo "Usage: "
  echo "  $0 <connection string to Oracle DB> <output file name> <table name> <run number>"
}

if test -z "$1" -o -z "$2" -o -z "$3" -o -z "$4" ;then usage; exit; fi

connstr="$1"
outfile="$2"
table="$3"
run="$4"

cat <<EOF | sqlplus -S "$connstr"
set colsep '|'
set echo off
set feedback off
set linesize 1000
set pagesize 0
set sqlprompt ''
set trimspool on
set headsep off
set embedded on

SPOOL $outfile;

select * from $table where IOV_ID=(select IOV_ID from MON_RUN_IOV where RUN_IOV_ID=(select IOV_ID from RUN_IOV where RUN_NUM=$run));
SPOOL OFF;
EOF
