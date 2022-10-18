#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################
#                                                                                   #
#           run_csoh.py: run Chandra State of Health script                         #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Oct 30, 2018                                               #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import time
import Chandra.Time
import maude
path = '/data/mta/Script/SOH/house_keeping/dir_list'
f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec "%s = %s" %(var, line)
#
#--- append path to a private folder
#
sys.path.append(bin_dir)

import copy_data_from_occ_part as cdfop


#-------------------------------------------------------------------------------
#-- run_csoh: run Chandra State of Health script                              --
#-------------------------------------------------------------------------------

def run_csoh():
    """
    run Chandra State of Health script
    input: none
    output: blob_<part>.json
    """

    cdfop.copy_data_from_occ_part('snap')

#-------------------------------------------------------------------------------

if __name__ == '__main__':

    run_csoh()
