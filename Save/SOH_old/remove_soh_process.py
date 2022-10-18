#!/bin/python

#################################################################################
#                                                                               #
#       remove_soh_process.py: remove run away SOH processes                    #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Jan 25, 2019                                           #
#                                                                               #
#################################################################################

import os
import sys
import re
import string
import time
import random
tail   = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(tail)

cmd    = 'ps aux | grep SOH > ' + zspace
os.system(cmd)

f    = open(zspace, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

cmd  = 'rm -rf ' + zspace
os.system(cmd)
#
#--- in normal case, there should be less than 10 processes running
#
if len(data) > 40:
    line = ''
    for ent in data:
        atemp = re.split('\s+', ent)
        line  = line + atemp[1] + ' ' 

    cmd = 'kill -9 ' + line
    os.system(cmd)
    print "SOH runaway processes terminated!!"
#
#--- reset running files so that the process can run correctly the next time
#
    house_keeping = '/data/mta/Script/SOH/house_keeping/'
    for run in ['running', 'running_snap', 'running_main']:
        ofile = house_keeping + run
        cmd   = 'rm -rf '   + ofile
        os.system(cmd)
        cmd   = 'echo 0 > ' + ofile
        os.system(cmd)
#
#--- sending a warning email to admin if the last email was sent more than two hours ago.
#
    wfile = house_keeping + 'runaway_check'
    f     = open(wfile, 'r')
    data  = [line.strip() for line in f.readlines()]
    f.close()
    ltime = int(data[0])
    stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    now   = Chandra.Time.DateTime(stday).secs
    diff  = now - ltime
    if diff > 2 * 3600:
        line = 'SOH runaway processes found. Check han-v.\n'
        fo   = open(zspace, 'w')
        fo.write(line)
        fo.close()

        cmd  = 'cat ' + zspace + '|mailx -s"SOH runaway processed detected" tisobe@cfa.harvard.edu'
        os.system(cmd)

        cmd  = 'rm -rf ' + zspace
        os.system(cmd)

        fo   = open(wfile, 'w')
        fo.write(now)
        fo.write('\n')
        fo.close()


