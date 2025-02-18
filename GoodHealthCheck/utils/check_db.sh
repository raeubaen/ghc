#!/bin/bash

usage(){
cat <<EOF
Usage: $0 user/password@db
EOF
exit 0
}

testdb(){
  echo "select sys_context('userenv','db_name') from dual;" | sqlplus -s $1
}

case $1 in 
  */*@*)
    testdb "$1"
  ;;
  *)
    usage
  ;;
esac
