#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################
#                                                                                   #
#           update_msididx_data.py: copy msididx.json from occ side                 #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Apr 10, 2019                                               #
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
path = '/data/mta/Script/SOH_TI/house_keeping/dir_list'
f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec "%s = %s" %(var, line)
#
#---- occ msididx location
#
url    = 'https://cxc.cfa.harvard.edu/mta/CSH/msididx.json'

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
#--- read the local limit table
#
    with open('./limit_table', 'r') as f:
        out = [line.strip() for line in f.readlines()]

        l_dict = {}
        for ent in out:
            atemp = re.split('<>', ent)
            l_dict[atemp[0]] = atemp[1:]
#
#--- read the last msididx.json from the main web site
#
    cmd = 'rm -rf  ./msididx.json'
    os.system(cmd)
    cmd = 'wget -q  ' + url + ' -Omsididx.json'
    os.system(cmd)
    with open('msididx.json', 'r') as f:
        data  = f.read()
    out = ast.literal_eval(data)

    updated = []
    for ent in out:

        msid = ent['name'].strip()
#
#--- find conversion value of the special msids
#
        conv = 1
        if ent['name'] in sp_msid:
            for k in range(0, len(sp_msid)):
                if msid == sp_msid[k]:
                    conv = conv_vals[k]
                    break
#
#--- update limit values
#
        try:
            out = l_dict[msid]
            save = []
            temp = {}
            lims = {}
            lims['cl']  = float(out[0]) * conv
            lims['ch']  = float(out[1]) * conv
            lims['wl']  = float(out[2]) * conv
            lims['wh']  = float(out[3]) * conv
            temp['set'] = lims
            save.append(temp)
            ent['lim'] = save
        except:
            pass

        updated.append(ent)
#
#--- special addtions
#
    t_add = [{"name": "AOACFIDC", "idx": 99999, \
              "description": "ACA Fiducial Object 0-7  (OBC)", "sc": [""]},\
             {"name": "AOACFCTC", "idx": 98989, \
              "description": "ACA Image Func 0-7 (OBC)",       "sc": [""]}\
            ]
#
#--- combine two lists
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

    data = read_file_data('/home/isobe/.netrc')

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
    data  = read_file_data(cfile)

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

def read_file_data(file):

    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    return data

#-------------------------------------------------------------------------------

if __name__ == '__main__':

    update_msididx_data()

