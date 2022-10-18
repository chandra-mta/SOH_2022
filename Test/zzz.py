#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

import sys
import re
import string
import math
import time
import Chandra.Time
import maude
import json
import random
path = '/data/mta/Script/SOH/house_keeping/dir_list'
with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append path to a private folder
#
sys.path.append(bin_dir)
mta_dir = '/data/mta/Script/Python3.6/MTA/'
sys.path.append(mta_dir)

import check_msid_status    as cms
import mta_common_functions as mcf


start = 694223994
stop  = 694310394
for k in range(1, 128):
    name = 'COSCS' + mcf.add_leading_zero(k, 3) + 'U'
    try:
        out = maude.get_msids('COSCS001', start, stop)
        val   = str((list(out['data'][0]['values']))[-1])
    except:
        print("NO DATA: " + str(name))

