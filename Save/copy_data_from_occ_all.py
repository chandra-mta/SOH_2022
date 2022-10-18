#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#   copy_data_from_occ.py: extract current SOH data from occ side                   #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Apr 11, 2019                                               #
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
import random
#
#---- local directory path
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

    import check_msid_status    as cms
#
#--- set a temporary file name
#
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)

#-------------------------------------------------------------------------------
#-- copy_data_from_occs: run infinite loop to extract blob and msididx data from occ side
#-------------------------------------------------------------------------------

def copy_data_from_occs():
    """
    run infinite loop to extract blob and msididx data from occ side
    input: none
    output: blob.json
            msididx.json
    """
#
#--- read msid list
#
    ifile     = house_keeping + 'msid_list'
    msid_list = read_data_file(ifile)
#
#--- msid <--> id dict
#
    ifile     = house_keeping + 'msid_id_list'
    data      = read_data_file(ifile)

    mdict     = {}
    for ent in data:
        atemp  = re.split(':', ent)
        mdict[atemp[0]] = atemp[1]
#
#--- read limit table
#
    ldict = read_limit_table()
#
#--- extract blob.json
#
    try:
        hold = run_extract_blob_data(msid_list, mdict, ldict)
    except:
        hold = 0

#-------------------------------------------------------------------------------
#-- run_extract_blob_data: extract current SOH data from occ side                 --
#-------------------------------------------------------------------------------

def run_extract_blob_data(msid_list, mdict, ldict):
    """
    extract current SOH data from occ side
    input:  msid_list   --- a list of soh related msids
            mdict       --- a dictionary of msid <--> id #
    output: blob.json   --- SOH data in json format
            hold        --- an indicator of whether the data is hold position: 0: no/1:yes
    """
    hold = 0
#
#--- check current time and set start and stop time
#
    stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    stop  = Chandra.Time.DateTime(stday).secs
    start = stop - 300
#
#--- check whether the data are currently coming from comm
#--- if not expand the data extraction period so that we can
#--- the last valid data value
#
    try:
        out   = maude.get_msids('AOPCADMD', start, stop)
        val   = str((list(out['data'][0]['values']))[-1])
        start = stop - 300

        if val == 'NaN':
#
#--- it seems that we are out of the comm; find the last valid data
#
            hold = long_blob_extraction(msid_list, mdict, ldict, stop)

        else:
#
#--- if it is currently in comm, run the loop for slightly shorter than 10 mins
#
            timeout = time.time() + 280
            while time.time() < timeout:
                stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
                stop  = Chandra.Time.DateTime(stday).secs
                start = stop - 300
                chk   = extract_blob_data(msid_list, mdict, ldict, start, stop)
#
#--- if comm stops, check the last 10 mins to find valid data
#
                if chk == 'stop':
                    start = stop - 600
                    chk   = extract_blob_data(msid_list, mdict, ldict, start, stop)
                    break
    except:
#
#--- currently we are outside of comm. if the last blob.json does not contain
#--- valid data, update
#
        hold = long_blob_extraction(msid_list, mdict, ldict, stop)

    return hold

#-------------------------------------------------------------------------------
#-- long_blob_extraction: extract current SOH data from occ side but outside of comm link
#-------------------------------------------------------------------------------

def long_blob_extraction(msid_list, mdict, ldict, stop):
    """
    extract current SOH data from occ side but outside of comm link
            ---- basically try to find the last valid data from the database
    input:  msid_list   --- a list of soh related msids
            mdict       --- a dictionary of msid <--> id #
            stop        --- stop time in seconds from 1998.1.1
    output: blob.json   --- SOH data in json format
            hold        --- an indicator of whether the data is hold position: 0: no/1:yes
    """
#
#--- telling the data extractiion is going on to the script which may start 
#--- while this extraction is still going on so that the other script won't start
#
#--- check blob.json has non-"NaN" values
#
    if check_blob_state() == 1:             #---- 1 means that blob.json needs update
        hold = 1
#
#--- if the blob.json is "empty" check 10 mins ago
#
        start = stop - 600 
        chk   =  extract_blob_data(msid_list, mdict, ldict, start, stop)
#
#--- if it is still "empty" try the last 12 hrs
#
        if chk == 'stop':
            start = stop - 43200
            chk = extract_blob_data(msid_list, mdict, ldict, start, stop)
#
#--- telling the long extraction is finished
#
    else:
        hold = 0
        
    return hold

#-------------------------------------------------------------------------------
#-- write_run_file: update running file to indicates data extraction is going on 
#-------------------------------------------------------------------------------

def write_run_file(chk, rfile='running'):
    """
    update running file to indicates data extraction is going on
    input:  chk     --- indicator: 0: not running/1: data extraction is going on
            rfile   --- indicator file name: defalut: running
    output: <house_keeping>/running --- udated file
    """
    out   = chk + '\n'
    ofile = house_keeping + rfile
    with open(ofile, 'w') as fo:
        fo.write(out)
    
    cmd = 'chmod 766 ' + ofile
    os.system(cmd)

#-------------------------------------------------------------------------------
#-- check_blob_state: check whether blob.json has none "NaN" values           --
#-------------------------------------------------------------------------------

def check_blob_state():
    """
    check whether blob.jzon has none "NaN" values
    input: none, but read from <data_dir>/blob.json
    ouput:  run --- 1: need update / 0: blob has non-"NaN" values
    """
    run = 0
    try:
        bfile = outdir + 'blob.json'
        data  = read_data_file(bfile)
    
        chk   = 0
        for ent in data:
            #mc1 = re.search('AOPCADMD', ent)
            #mc2 = re.search('CIUB',     ent)
            #mc3 = re.search('EB1K1',    ent)
            #if (mc1 is not None) or (mc2 is not None) or (mc3 is not None):
            try:
                mc   = re.search('AOGBIAS1', str(ent))
            except:
                continue
            if mc is not None:
                mcv  = re.search('"value":"NaN"', ent)
                chk += 1
                if mcv is not None:
                    run = 1
                    break
                else:
#
#--- even if the msid has a valid value, if the file is not updated more than 3 hrs
#--- update blob.json, just in a case, for some unknown reasons, it is not updated
#
                    if find_last_upate(bfile) == 1:
                        run = 1

                    else:
                        run = 0
                        if chk == 0:
                            continue
                    break
            else:
                run = 1
    except:
        run = 1

    return run

#-------------------------------------------------------------------------------
#-- find_last_upate: check the last update and if it is more than tsapn sec ago, notify 
#-------------------------------------------------------------------------------

def find_last_upate(tfile, tspan=10800):
    """
    check the last update and if it is more than tspan secs ago, notify
    input:  tfile   --- a file to be checked; 
            tspan   --- a time span in seconds; default is 3 hrs
    ouptput:    0 or 1. 1 indicates that more than tsapn secs passed from the last update
    """
#
#--- current time
#
    ctime = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    ctime = Chandra.Time.DateTime(ctime).secs
#
#--- last fine update time
#
    btime = time.strftime("%Y:%j:%H:%M:%S", time.gmtime(os.path.getmtime(tfile)))
    btime = Chandra.Time.DateTime(btime).secs

    tdiff = ctime - btime

    if tdiff > tspan:
        return 1
    else:
        return 0

#-------------------------------------------------------------------------------
#-- extract_blob_data: extract current SOH data from occ side                 --
#-------------------------------------------------------------------------------

def extract_blob_data(msid_list, mdict, ldict, start, stop):
    """
    extract current SOH data from occ side
    input:  msid_list   --- a list of soh related msids
            mdict       --- msid <---> id dicct
            start       --- starting time
            stop        --- stopping time
    output: blob.json   --- SOH data in json format
    """
#
#--- check the most recent data and see whether it is a valid data
#--- if not just go back
#
    try:
        out   = maude.get_msids('AOPCADMD', start, stop)
        val   = str((list(out['data'][0]['values']))[-1])
        if val == 'NaN':
            return 'stop'
#
#--- find the most rescent updated time
#
        ctime = str((list(out['data'][0]['times']))[-1])
        ctime = Chandra.Time.DateTime(ctime).date
        ctime = ctime.replace(':', '')
    except:
        ###ctime = time.strftime("%Y%j%H%M%S", time.gmtime())
        return 'stop'

    mlen  = len(msid_list)
    mlst  = int(mlen/100) + 1
    mstp  = mlen -1
#
#--- extract data using maude tool; 100 msids at a time
#
    findx = 99998
    line  = '[\n'
    for  k in range(0, mlst):
        mstart     = k * 100
        mstop      = mstart + 100
#
#--- the last round has fewer than 100 msids
#
        if mstop > mlen:
            mstop  = mlen

        msid_short = msid_list[mstart:mstop]
#
#---- maude tool
#
        try:
            mdata = maude.get_msids(msid_short, start, stop)
        except:
            continue
#
#--- now extract data and put into json data format
#
        for nk in range(0, len(msid_short)):
            try:
                msid = str(mdata['data'][nk]['msid'])
            except:
                continue
            try:
                val  = str((list(mdata['data'][nk]['values']))[-1])
            except:
                val = 'NaN'
#
#--- unit conversion for a few special cases
#
            if msid.upper() in ['2DETART', '2SHLDART']:
                val = str(int(float(val) / 256.0))
            elif msid.upper() == 'AOACINTT':
                val = "%1.4f" % (float(val) / 1000.0)
            elif msid.upper() in ['AOGBIAS1', 'AOGBIAS2', 'AOGBIAS3', 'AORATE1', 'AORATE2', 'AORATE3']:
                val = "%1.3f" % (float(val) * 206264.98)    #----arcsec/sec
            elif msid.upper() in ['AODITHR2', 'AODITHR3']:
                val = "%1.3f" % (float(val) * 3600.0)  
            elif msid.upper() in ['AACCCDPT']:
                val = "%1.3f" % (5.0 * (float(val) -32) / 9.0)      #--- convert from F to C

            val = '"' + val + '"'
            try:
                index  = mdict[msid]
            except:
                index  = '"0000"'
    
            sval   = val.replace('\"', '')
            status = check_status(msid, sval, ldict)

            out = '{"msid":"' + msid + '",'
            out = out + '"index":"'  + index + '",'
            out = out + '"time":"'   + ctime + '",'
            out = out + '"value":'   + val  + ','
            out = out + '"status":"' + status  + '",'
#
#--- if it is the last entry, do without ','
#
#            if m == mstp:
#                out = out + '"f": '     + '"1"}'
#            else:
#                out = out + '"f": '     + '"1"},'
     
            out  = out + '"f": '     + '"1"},'
            line = line  + out + "\n"
#
#---- special computed values
#
    [aoacfid, aoacfct] = get_aoacomputed(start, stop, ctime)
             
    line = line + aoacfid + '\n'
    line = line + aoacfct + '\n'

    line = line + ']'

    out  = outdir + 'blob.json'
    with open(out, 'w') as fo:
        fo.write(line)

    return 'run'

#-------------------------------------------------------------------------------
#-- get_aoacomputed: adding computerd AOACFID and AOACFCT to the database     --
#-------------------------------------------------------------------------------

def get_aoacomputed(start, stop, ctime):
    """
    adding computerd AOACFID and AOACFCT to the database
    input:  start   --- start time
            stop    --- stop time
            ctime   --- time to be display
    output: aoacfid --- AOACFID output in blob format
            aoacfct --- AOACFCT output in blob format
    """

    msid_short = ['AOACFID0', 'AOACFID1','AOACFID2','AOACFID3','AOACFID4','AOACFID5','AOACFID6','AOACFID7']
    aoacfid    = create_aoaline(msid_short, start, stop, 'AOACFIDC', 99999, ctime, mlast=0)

    msid_short = ['AOACFCT0', 'AOACFCT1','AOACFCT2','AOACFCT3','AOACFCT4','AOACFCT5','AOACFCT6','AOACFCT7']
    aoacfct    = create_aoaline(msid_short, start, stop, 'AOACFCTC', 98989, ctime, mlast=1)


    return [aoacfid, aoacfct]

#-------------------------------------------------------------------------------
#-- create_aoaline: create a combined blob data line                         ---
#-------------------------------------------------------------------------------

def create_aoaline(msid_short,start, stop, msid, index, ctime, mlast=0):
    """
    create a combined blob data line 
    input:  msid_short  --- a list of msids to be used
            start       --- start time
            stop        --- stop time
            ctime       --- time to be display
            msid        --- msid to be used
            index       --- index of the msid
            mlast       --- indicator of whether this is the last of the blob entry
                            if so, it cannot have "," at the end
    output: out         --- blob data line
    """

    mdata = maude.get_msids(msid_short, start, stop)
    line = ''
    for k in range(0, 8):
        val = str((list(mdata['data'][k]['values']))[-1])
        line = line + str(val)[0]

    out = '{"msid":"' + msid + '",'
    out = out + '"index":"' + str(index) + '",'
    out = out + '"time":"'  + ctime + '",'
    out = out + '"value":"'  + line  + '",'
    if mlast == 1:
        out = out + '"f": '     + '"1"}'
    else:
        out = out + '"f": '     + '"1"},'


    return out

#-------------------------------------------------------------------------------
#-- copy_msididx_data: copy msididx.json from occ side                        --
#-------------------------------------------------------------------------------

def copy_msididx_data():
    """
    copy msididx.json from occ side
    input: none but read from <url>
    output: <outdir>/msididx.json
    """
    [usr, pwd] = get_u_p()

    cmd = 'rm ./msididx.json'
    os.system(cmd)
    cmd = 'wget --user='+usr + ' --password=' + pwd + '  ' + url
    os.system(cmd)
#
#--- special addtions
#
    line = '[{"name": "AOACFIDC", "idx": 99999, "description": "ACA Fiducial Object 0-7  (OBC)", "sc": [""]},'
    line = line + '{"name": "AOACFCTC", "idx": 98989, "description": "ACA Image Func 0-7 (OBC)", "sc": [""]},{"name"'

    with open('msididx.json', 'r') as f:
        data = f.read()

    out = data.replace('[{"name"', line)

    outfile = outdir + 'msididx.json'
    with  open(outfile, 'w') as fo:
        fo.write(out)


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
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def check_status(msid, val, ldict):

    limit   = ldict[msid]
    print("I AM HERE: " + msid + '<-->' + str(val) +  '<-->' + str(limit))
    if (len(limit) == 0) or (limit == ['']):
        print("I AM HERE G1")
        return "GREEN"
    else:
        try:
            nval = float(val)
            ly   = float(limit[0])
            uy   = float(limit[1])
            lr   = float(limit[2])
            ur   = float(limit[3])
            if (nval > ly) and (nval < uy):
                print("I AM HERE G2")
                return "GREEN"
            elif (nval > lr) and (nval < ur):
                print("I AM HERE C1")
                return "CAUTION"
            else:
                print("I AM HERE W")
                return "WARNING"
        except:
            if val in ['ERR', 'FALT', 'FAIL']:
                print("I AM HERE C2")
                return "CAUTION"
            if val in limit:
                print("I AM HERE G3")
                return "GREEN"
            else:
                print("I AM HERE C3")
                return "CAUTION"

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def string_to_list(line):
    line.strip()


    return alist

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def read_data_file(ifile):

    with open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    return data

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    copy_data_from_occs()

#
#--- check whether a long blob extraction is currently running; if so, stop
#
##    ifile   = house_keeping + 'running'
##    running = read_data_file(ifile)
##
##    try:
##        if running[0] == '1':
##            exit(1)
##        else:
##            write_run_file('1')
##    except:
##        write_run_file('0')
##        exit(1)
##
##    try:
##        copy_data_from_occs()
##    except:
##        pass
##
##    write_run_file('0')
