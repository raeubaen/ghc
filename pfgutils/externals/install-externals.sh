#!/bin/bash

curdir=$PWD
nproc=$(grep -c proc /proc/cpuinfo)
export CFLAGS="$CFLAGS -fPIC"
export CXXFLAGS="$CXXFLAGS -fPIC"

install_postgres(){
  wget -O $curdir/postgresql.tar.gz ftp://ftp.postgresql.org/pub/source/v8.4.22/postgresql-8.4.22.tar.gz
  mkdir -p $curdir/postgresql-source
  tar -xzf $curdir/postgresql.tar.gz --strip-components=1 -C $curdir/postgresql-source
  cd $curdir/postgresql-source
  ./configure --prefix=$curdir/postgresql
  make -j $nproc install
  cd -
  rm -rf $curdir/postgresql-source
}

install_pqxx(){
  wget -O $curdir/libpqxx.tar.gz http://pqxx.org/download/software/libpqxx/libpqxx-4.0.tar.gz
  mkdir -p $curdir/libpqxx-source
  tar -zxf $curdir/libpqxx.tar.gz -C $curdir/libpqxx-source --strip-components=1
  cd $curdir/libpqxx-source
  ./configure --prefix=$curdir/libpqxx
  make -j $nproc install
  cd -
  rm -rf $curdir/libpqxx-source
  
}

install_psycopg2(){
  wget -O $curdir/psycopg2.tar.gz https://github.com/psycopg/psycopg2/archive/2_6_1.tar.gz
  mkdir -p $curdir/psycopg2
  tar -xzvf $curdir/psycopg2.tar.gz --strip-components=1 -C $curdir/psycopg2
  cd $curdir/psycopg2
  python setup.py build_ext --inplace
}

test -d $curdir/postgresql || install_postgres
export PATH=$curdir/postgresql/bin:$PATH
test -d $curdir/libpqxx  || install_pqxx
test -d $curdur/psycopg2 || install_psycopg2
