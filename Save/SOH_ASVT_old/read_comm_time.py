#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################
#                                                                                   #
#           read_comm_time.py: read comm time from aspect site                      #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Jan 18, 2018                                               #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import time
import Chandra.Time
#
path = '/data/mta/Script/SOH_ASVT/house_keeping/dir_list'
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
#
#--- set a temporary file name
#
rtail  = int(time.time())
zspace = '/tmp/zspace' + str(rtail)

#-------------------------------------------------------------------------------
#-- find_comm_pass: read comm pass from aspect site                           --
#-------------------------------------------------------------------------------

def find_comm_pass():
    """
    read comm pass form aspect site
    input:  none but read from http://cxc.harvard.edu/mta/ASPECT/arc/'
    output: ./comm_list --- <start time>\t<start time in sec>\t<steop time in sec>
    """

    now = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    now = Chandra.Time.DateTime(now).secs

    cmd = 'wget -q -O' + zspace + ' http://cxc.harvard.edu/mta/ASPECT/arc/'
    os.system(cmd)

    f    = open(zspace, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    outfile = house_keeping + 'comm_list'
    fo   = open(outfile, 'w')
    for ent in data:
        mc  = re.search('Comm pass', ent)
        if mc is not None:
            atemp = re.split('<tt>', ent)
            btemp = re.split('<\/tt>', atemp[1])
            ctime = btemp[0]

            atemp = re.split('duration', ent)
            btemp = re.split('\)', atemp[1])
            dur   = (btemp[0].strip())
            atemp = re.split(':', dur)
            dur   = int((float(atemp[0]) + float(atemp[1]) / 60.0) * 3600.0)

            start = int(Chandra.Time.DateTime(ctime).secs)
            stop  = start + dur

            if stop < now:
                continue

            line  = ctime + '\t' + str(start) + '\t' + str(stop) + '\n'
            fo.write(line)

    fo.close()

#-------------------------------------------------------------------------------

if __name__ == "__main__":

    find_comm_pass()
