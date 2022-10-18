#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#           update_msididx_data.py: copy msididx.json from occ side                 #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Mar 29, 2019                                               #
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
import ast
import json
path = '/data/mta/Script/SOH3/house_keeping/dir_list'
with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#---- occ msididx location
#
url    = 'https://occweb.cfa.harvard.edu/occweb/web/fot_web/software/sandbox/SOT_area/msididx.json'

sp_msid       = ['AOGBIAS1', 'AOGBIAS2', 'AOGBIAS3', 'AORATE1', 'AORATE2', 'AORATE3', 'AODITHR2', 'AODITHR3']
conv_vals     = [206264.98,   206264.98,  206264.98, 206264.98,  206264.98, 206264.98, 3600,0,     3600.0]

#-------------------------------------------------------------------------------
#-- update_msididx_data: copy msididx.json from occ side                        --
#-------------------------------------------------------------------------------

def update_msididx_data():
    """
    copy msididx.json from occ side
    input: none but read from <url>
    output: <html_dir>/msididx.json
    """
#
#--- only when it is in comm, update 
#
    if check_whether_in_comm() == 0:
        exit(1)
#
#--- during the comm, update the data only once 5 mins
#
    ifile = house_keeping + 'msididx_time'
    with open(ifile, 'r') as f:
        ptime = f.read()
    
    ptime = float(ptime.strip()) + 300.0
    now   = time.time()
    if now < ptime:
        exit(1)
    else:
        with  open(ifile, 'w') as fo:
            line = str(now) + '\n'
            fo.write(line)
#
#--- start the main part
#
    [usr, pwd] = get_u_p()

    cmd = 'rm ./msididx.json'
    os.system(cmd)
    cmd = 'wget -q --user='+usr + ' --password=' + pwd + '  ' + url
    os.system(cmd)
#
#--- special addtions
#
    t_add = [{"name": "AOACFIDC", "idx": 99999, "description": "ACA Fiducial Object 0-7  (OBC)", "sc": [""]},\
             {"name": "AOACFCTC", "idx": 98989, "description": "ACA Image Func 0-7 (OBC)",       "sc": [""]}]

    with open('msididx.json', 'r') as f:
        data  = f.read()
#
#--- convert limit values for the specail msids
#
    sp_len = len(sp_msid)                   #--- numbers of the specai msids

    out = ast.literal_eval(data)
    updated = []
    for ent in out:
        if ent['name'] in sp_msid:
#
#--- find conversion value for the msid
#
            chk = 0
            for k in range(0, sp_len):
                if ent['name'] == sp_msid[k]:
                    conv = conv_vals[k]
                    chk  = 1
                    break
            if chk > 0:
#
#--- check whether the data set actually has the limit restrictions
#
                try:
                    out1 = ent['lim']
                except:
                    updated.append(ent)
                    continue
#
#--- there could be more than one set of limit tables
#
                save = []
                chk  = 0
                for ent1 in out1:
#
#--- again, make sure that it has the table
                    try:
                        out2 = ent1['set']
                    except:
                        chk  = 1
                        break
    
                    temp = {}
                    lims = {}
                    lims['ch']  = float(out2['ch']) * conv
                    lims['wl']  = float(out2['wl']) * conv
                    lims['wh']  = float(out2['wh']) * conv
                    lims['cl']  = float(out2['cl']) * conv
                    temp['set'] = lims
                    save.append(temp)
                if chk == 0:
                    ent['lim'] = save
                updated.append(ent)
            else:
                updated.append(ent)
        else:
            updated.append(ent)
#
#--- convine two lists
#
    out  = t_add + updated
#
#--- print out the data
#
    outfile = html_dir + 'msididx.json'
    with open(outfile, 'w') as msididx:
        json.dump(out, msididx)


#-------------------------------------------------------------------------------
#-- get_u_p: get login information                                            --
#-------------------------------------------------------------------------------

def get_u_p():
    """
    get login information
    input: none
    output: user    --- user name
            pawd    --- password
    """

    data = read_data_file('/home/isobe/.netrc')

    for line in data:
        mc1 = re.search('login', line)
        mc2 = re.search('pass', line)
        if mc1 is not None:
            atemp = re.split('\s+', line)
            user  = atemp[1]
        elif mc2 is not None:
            atemp = re.split('\s+', line)
            pwd   = str(atemp[1].strip())

    return [user, pwd]

#-------------------------------------------------------------------------------
#-- check_whether_in_comm: check whether chandara is in comm link             --
#-------------------------------------------------------------------------------

def check_whether_in_comm():
    """
    check whether chandara is in comm link
    input:  none
    output: comm; 0: no / 1: yes
    """

    cfile = house_keeping + 'comm_list'
    data  = read_data_file(cfile)

    tday  = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    tnow  = Chandra.Time.DateTime(tday).secs

    comm  = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        start = float(atemp[1])
        stop  = float(atemp[2])
        if (tnow >= start) and (tnow < stop):
            comm = 1
            break

    return comm

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def read_data_file(ifile):

    with open(ifile, 'r')
        data = [line.strip() for line in f.readlines()]

    return data

#-------------------------------------------------------------------------------

if __name__ == '__main__':

    update_msididx_data()

