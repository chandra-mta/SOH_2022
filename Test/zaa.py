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


ifile = '/data/mta/Script/SOH/house_keeping/Inst_part/msid_id_list_all'
data  = mcf.read_data_file(ifile)

save = []
for ent in data:
    mc   = re.search('COSCS', ent)
    if mc is not None:
        atemp = re.split(':', ent)
        msid  = atemp[0]
        sid   = atemp[1]
        if msid[-1] == 'S':
            save.append(msid)

save = sorted(save)
for ent in save:
    print(ent)

