#!/bin/sh

mount | grep -q '/cvmfs/cms.cern.ch' && export TNS_ADMIN=/cvmfs/cms.cern.ch/slc6_amd64_gcc491/cms/oracle-env/29/etc || export TNS_ADMIN=$(cd $(dirname ${BASH_SOURCE}); pwd -P)
