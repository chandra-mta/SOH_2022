#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import time
import Chandra.Time
import sqlite3
import json
#
path = '/data/mta/Script/SOH3/house_keeping/dir_list'
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
#
#--- set a temporary file name
#
import random
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)

glimmon = '/data/mta4/MTA/data/op_limits/glimmondb.sqlite3'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def get_current_limits():

    m_dict = get_msididx()

    ifile = house_keeping + 'msid_list'
    data  = read_data_file(ifile)

    sline  = ''
    for msid in data:
#        if msid[-1] in ['T', 't']:
#            tind = 1
#        else:
#            tind = 0
        tind = 0

        line =  msid 

        out = read_glimmon(msid, tind)
        if len(out) > 0:
           for val in out:
               line = line + '<>' + str(val)
            
           line = line + '\n'
           sline = sline + line

    with open('limit_table', 'w') as fo:
        fo.write(sline)


#-----------------------------------------------------------------------------------
#-- read_glimmon: read glimmondb.sqlite3 and return yellow and red lower and upper limits 
#-----------------------------------------------------------------------------------

def read_glimmon(msid, tind):
    """
    read glimmondb.sqlite3 and return yellow and red lower and upper limits
    input:  msid--- msid
    tind--- whether this is a temperature related msid and in K. O; no, 1: yes
    output: y_min   --- lower yellow limit
    y_max   --- upper yellow limit
    r_min   --- lower red limit
    r_max   --- upper red limit
    """
    
    lmsid = msid.lower()
#
#--- glimmon keeps the temperature related quantities in C. convert it into K.
#
    if tind == 0:
        add = 0
    else:
        add = 273.15
    
    db = sqlite3.connect(glimmon)
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM limits WHERE msid='%s'" % lmsid)
    allrows = cursor.fetchall()
    
    if len(allrows) == 0:
        return []
    
    tup   = allrows[0]
    try:
        if msid == 'AACCCDPT':
            y_min = f_to_c(tup[12])
            y_max = f_to_c(tup[11])
            r_min = f_to_c(tup[14])
            r_max = f_to_c(tup[13])
        elif msid in ['AODITHR1', 'AODITHR2', 'AODITHR3']:
            y_min = tup[12] * 3600.0
            y_max = tup[11] * 3600.0
            r_min = tup[14] * 3600.0
            r_max = tup[13] * 3600.0
        elif msid in ['AORATE1', 'AORATE2', 'AOGBIAS1', 'AOGBIAS2', 'AOGBIAS3']:
            y_min = tup[12] * 206265.0
            y_max = tup[11] * 206265.0
            r_min = tup[14] * 206265.0
            r_max = tup[13] * 206265.0
        else:
            y_min = tup[12] + add
            y_max = tup[11] + add
            r_min = tup[14] + add
            r_max = tup[13] + add
    except:
        y_min = tup[12]
        y_max = tup[11]
        r_min = tup[14]
        r_max = tup[13]
    
    return [y_min, y_max, r_min, r_max]

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def f_to_c(fval):
    
    return 5.0 * (fval - 32.0) / 9.0


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def get_msididx():

    with open('/data/mta4/www/CSH/msididx.json', 'r') as f:
        data = json.load(f)

    m_dict = {}
    for ent in data:
        try:
            m_dict[ent['name']] = str(ent['sc'])
        except:
            continue

    return m_dict

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):

    with open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    if remove  == 1:
        cmd = 'rm -rf ' + ifile
        os.system(cmd)

    return data



#-------------------------------------------------------------------------------

if __name__ == "__main__":

    get_current_limits()

