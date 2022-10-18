#!/usr/bin/env /data/mta4/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#           copy_data_from_occ_part.py: extract blob for specific part from occ     #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Nov 03, 2020                                               #
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
import json
import random
path = '/data/mta4/Script/SOH/house_keeping/dir_list'
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
#-- copy_data_from_occ_part: run loop to extract blob for a specific part from occ using maude
#-------------------------------------------------------------------------------

def copy_data_from_occ_part(part):
    """
    run loop to extract blob for a specific part from occ using maude
    input: part --- which group (such as snap)
    output: blob_<part>.json
    """
#
#--- set user and password for maude
#
    global user, password
    [user, password] = read_nfile()
#
#--- read msid list
#
    ifile     = house_keeping + 'Inst_part/msid_list_' + part
    msid_list = read_data_file(ifile)
#
#--- msid <--> id dict
#
    ifile     = house_keeping + 'Inst_part/msid_id_list_' + part
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
#--- extract blob_<part>.json
#
    try:
        hold = run_extract_blob_data(msid_list, mdict, part, ldict)
    except:
        hold = 0

#-------------------------------------------------------------------------------
#-- run_extract_blob_data: extract current SOH data from occ side                 --
#-------------------------------------------------------------------------------

def run_extract_blob_data(msid_list, mdict, part, ldict):
    """
    extract current SOH data from occ side
    input:  msid_list      --- a list of soh related msids
            mdict               --- a dictionary of msid <--> id #
            part                --- the name of the instrument group
    output: blob_<part>.json    --- SOH data in json format
            hold                --- an indicator of whether the data is 
                                    hold position: 0: no/1:yes
    """
    com_time = chk_time_to_comm()
    hold = 0
#
#--- check current time and set start and stop time
#
    stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    stop  = Chandra.Time.DateTime(stday).secs
    start = stop - 60
#
#--- check whether the data are currently coming from comm
#--- if not expand the data extraction period so that we can
#--- the last valid data value
#
    try:
        out   = maude.get_msids('AOGBIAS1', start, stop)
        val   = str((list(out['data'][0]['values']))[-1])
        start = stop - 60

        if val == 'NaN':
#
#--- it seems that we are out of the comm; find the last valid data
#--- unless the next comm is coming less than 4  mins
#
            if com_time > 240:
                hold = long_blob_extraction(msid_list, mdict,ldict,  stop)
        else:
#
#--- if it is currently in comm, run the loop for slightly shorter than 5 mins
#
            timeout = time.time() + 290
            while time.time() < timeout:
                stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
                stop  = Chandra.Time.DateTime(stday).secs
                start = stop - 60
                chk   = extract_blob_data(msid_list, mdict, ldict, start, stop, part)
#
#--- if comm stops, check the last 10 mins to find valid data
#
                if chk == 'stop':
                    start = stop - 600
                    chk   = extract_blob_data(msid_list, mdict, ldict, start, stop, part)
                    break
#
#--- keep time record so that we know when the last comm data update happened
#
                update_last_blob_check(part, stday)
#
#--- currently we are outside of comm. if the last blob_<part>.json does not contain
#--- valid data, update
#
    except:
        if com_time > 240:
            hold = long_blob_extraction(msid_list, mdict, ldict, stop, part)

    return hold

#-------------------------------------------------------------------------------
#-- long_blob_extraction: extract current SOH data from occ side but outside of comm link
#-------------------------------------------------------------------------------

def long_blob_extraction(msid_list, mdict, ldict, stop, part):
    """
    extract current SOH data from occ side but outside of comm link
            ---- basically try to find the last valid data from the database
    input:  msid_list    --- a list of soh related msids
            mdict             --- a dictionary of msid <--> id #
            stop              --- stop time in seconds from 1998.1.1
            part              --- the name of the instrument group
    output: blob_<part>.json  --- SOH data in json format
            hold              --- an indicator of whether the data is hold position: 0: no/1:yes
    """
#
#--- telling the data extractiion is going on to the script which may start 
#--- while this extraction is still going on so that the other script won't start
#
#
#--- check blob_<part>.json has non-"NaN" values
#
    if check_blob_state(part) == 1:             #---- 1 means that blob_<part>.json needs update
        hold = 1
#
#--- if the blob_<part>.json is "empty" check 10 mins ago
#
        start = stop - 600 
        chk   =  extract_blob_data(msid_list, mdict, ldict, start, stop, part)
#
#--- if it is still "empty" try the last 12 hrs
#
        if chk == 'stop':
            start = stop - 43200
            chk = extract_blob_data(msid_list, mdict, ldict, start, stop, part)
#
#--- telling the long extraction is finished
#
    else:
        hold = 0

    return hold

#-------------------------------------------------------------------------------
#-- write_run_file: update running_<part> file to indicates data extraction is going on 
#-------------------------------------------------------------------------------

def write_run_file(chk, part):
    """
    update running_<part> file to indicates data extraction is going on
    input:  chk     --- indicator: 0: not running_<part>/1: data extraction is going on
            part    --- the name of the instrument group
    output: <house_keeping>/running_<part> --- udated file
    """
    out   = chk + '\n'
    ofile = house_keeping + 'running_' + part

    with open(ofile, 'w') as fo:
        fo.write(out)
    
    cmd = 'chmod 777 ' + ofile
    os.system(cmd)

#-------------------------------------------------------------------------------
#-- check_blob_state: check whether blob.json has none "NaN" values           --
#-------------------------------------------------------------------------------

def check_blob_state(part):
    """
    check whether blob.json has none "NaN" values
    input: part --- the name of the instrument group
    ouput:  run --- 1: need update / 0: blob has non-"NaN" values
    """
    run = 0
    try:
        bfile = html_dir + 'blob_' + part + '.json'
        data  = read_data_file(bfile)
    
        chk   = 0
        for ent in data:
            try:
                mc   = re.search('AOGBIAS1', str(ent))
            except:
                continue

            if mc is not None:
                mcv  = re.search('"value":"NaN"', str(ent))
                chk += 1
                if mcv is not None:
                    run = 1
                    break
                else:
#
#--- every 400 secs, update dummy time stamp etnry in blob data file
#
                    if find_last_upate(bfile, tspan=400) == 1:
                        update_lastdcheck_entry()
#
#--- even if the msid has a valid value, if the real msid data are not updated more than 3 hrs
#--- update blob_<part>.json, just in a case, the data was not updated for some unknown reasons.
#
                        tfile = house_keeping + part + '_last_check'
                        if find_last_upate(tfile) == 1:
                            stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
                            update_last_blob_check(part, stday)
                            run = 1

                    elif find_last_upate(bfile) == 1:
                        stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
                        update_last_blob_check(part, stday)
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
    try:
        btime = time.strftime("%Y:%j:%H:%M:%S", time.gmtime(os.path.getmtime(tfile)))
        btime = Chandra.Time.DateTime(btime).secs
    except:
        btime = 0

    tdiff = ctime - btime

    if tdiff > tspan:
        return 1
    else:
        return 0


#-------------------------------------------------------------------------------
#-- extract_blob_data: extract current SOH data from occ side                 --
#-------------------------------------------------------------------------------

def extract_blob_data(msid_list, mdict, ldict, start, stop, part):
    """
    extract current SOH data from occ side
    input:  msid_list           --- a list of soh related msids
            mdict               --- msid <---> id dict
            start               --- starting time
            stop                --- stopping time
            part                --- instrument name
    output: blob_<part>.json    --- SOH data in json format
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
#--- mlist: a list of valid msids / vdict: a dict of msid <--> current value
#
    mlist = []
    vdict = {}
#
#--- extract data using maude tool; 100 msids at a time
#
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
                msid = str(mdata['data'][nk]['msid']).upper()

            except:
                continue
            try:
                val  = str((list(mdata['data'][nk]['values']))[-1])
            except:
                val = 'NaN'
#
#--- unit conversion for a few special cases
#
            if msid in ['2DETART', '2SHLDART', '2DETBRT', '2SHLDBRT']:
                val = "%3.1f " % round((float(val) / 256.0), 2)

            elif msid == 'AOACINTT':
                val = "%1.4f" % (float(val) / 1000)

            elif msid in ['AOGBIAS1', 'AOGBIAS2', 'AOGBIAS3', 'AORATE1', 'AORATE2', 'AORATE3']:
                val = "%1.3f" % (float(val) * 206264.98)    #----arcsec/sec

            elif msid in ['AODITHR2', 'AODITHR3']:
                val = "%1.3f" % (float(val) * 3600.0)  

            elif msid in ['AACCCDPT']:
                val = "%1.3f" % (5.0 * (float(val) -32) / 9.0)      #--- convert from F to C

            elif msid in ['EOCHRGB1', 'EOCHRGB2', 'EOCHRGB3']:      #--- percentage
                val = "%d" % (float(val) * 100.0)  
                

            mlist.append(msid)
            vdict[msid] = val
#
#--- create "ACIS Stat7-0" msid
#
    if part == 'snap':
        msid = 'ACISSTAT'
        try:
            val = ''
            for name in ['1STAT7ST', '1STAT6ST', '1STAT5ST', '1STAT4ST',\
                         '1STAT3ST', '1STAT2ST', '1STAT1ST', '1STAT0ST']:
                val = val + covert_to_tf(vdict[name])
        except:
            val  = 'NaN'
        mlist.append(msid)
        vdict[msid] = val
        mdict[msid] = '97995'
#
#--- create json output
#
    findx = 99998
    line  = '[\n'
    for msid in mlist:
        val = vdict[msid]
        val = '"' + val + '"'
        try:
            index  = mdict[msid]
        except:
            index  = str(findx)
            findx -= 1

        try:
            sval = val.replace('\"', '')
            status = cms.check_status(msid, sval, ldict, vdict)
        except:
            status ='GREEN'

        out = '{"msid":"' + msid + '",'
        out = out + '"index":"' + index + '",'
        out = out + '"time":"'  + ctime + '",'
        out = out + '"value":'  + val  + ','
        out = out + '"scheck":"' + status + '",'
#
#--- if it is the last entry, do without ','
#
        out  = out + '"f": '     + '"1"},'
        line = line  + out + "\n"
#
#---- special computed values
#
    [aoacfid, aoacfct] = get_aoacomputed(start, stop, ctime)
             
    line = line + update_dummy_entry() + '\n'
    line = line + aoacfid + '\n'
    line = line + aoacfct + '\n'

    line = line + ']'

    out  = html_dir + 'blob_' + part + '.json'
    with open(out, 'w') as fo:
        fo.write(line)

    return 'run'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def covert_to_tf(val):

    if float(val) == 1:
        return 'T'
    else:
        return 'F'

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
#-- update_dummy_entry: create a dummy msid data line                         --
#-------------------------------------------------------------------------------

def update_dummy_entry():
    """
    create a dummy msid data line
    input:  none
    output: dummry msid (LASTDCHECK) data line
    """

    dtime = time.strftime("%Y-%m-%dT%H:%Mz", time.gmtime())
    rtime = time.strftime("%Y%j%H%M%S.000", time.gmtime())
    line  = '{"msid":"LASTDCHECK","index":"97989","time":"' + str(rtime) + '",' 
    line  = line + '"value":"' + str(dtime) + '","f":"1"},'

    return line

#-------------------------------------------------------------------------------
#-- read_limit_table: read limit table and create msid <---> limit dictionary -
#-------------------------------------------------------------------------------

def read_limit_table():
    """
    read limit table and create msid <---> limit dictionary
    this gives only neumeric cases
    input:  none but read from <house_keeping>/limit_table
    output: ldict   --- dictionary of msid <---> limits
    """
    ifile = house_keeping + 'limit_table'
    out   = read_data_file(ifile)
    ldict = {}
    for line in out:
        atemp = re.split('<>', line)
        olist = []
        for val in atemp[1:]:
            try:
                val = float(val)
            except:
                try:
                    val = val.replace("\'", '')
                except:
                    pass
            olist.append(val)
        ldict[atemp[0]] = olist

    return ldict

#-------------------------------------------------------------------------------
#-- update_lastdcheck_entry: update dummy entry line                          --
#-------------------------------------------------------------------------------

def update_lastdcheck_entry(part):
    """
    update dummy entry line
    input:  part    --- data part name
    output: data file with the updated dummy msid entry line
    """

    bfile = html_dir + 'blob_' + part + '.json'
    data  = read_data_file(bfile)

    mc    = re.search('LASTDCHECK', data[-3])
    if mc is not none:
        data[-3] = update_dummy_entry()
    else:
        data.insert(-3, update_dummy_entry())

    line = ''
    for ent in data:
        line = line + ent + '\n'

    with open(bfile, 'w') as fo:
        fo.write(line)

#-------------------------------------------------------------------------------
#-- update_last_blob_check: keep the record of the last time blob data are checked
#-------------------------------------------------------------------------------

def update_last_blob_check(part, stday):
    """
    keep the record of the last time blob data are checked
    input:  part    --- instrument group name
            stday   --- time stamp
    output: <house_keeping>/<part>_last_check
    """

    tfile = house_keeping + part + '_last_check'
    cmd = 'rm -rf ' + tfile
    os.system(cmd)
    cmd = 'echo ' + str(stday) + '> ' + tfile
    os.system(cmd)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def chk_time_to_comm():
    ifile    = house_keeping + 'stime_to_comm'
    out      = read_data_file(ifile)
    com_time = float(out[0])

    return com_time

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def read_nfile():

    ifile = house_keeping + '.netrc'
    data  = read_data_file(ifile)
    for ent in data:
        atemp = re.split('\s+', ent)
        if atemp[0] == 'login':
            user = atemp[1]
        elif atemp[0] == 'password':
            password = atemp[1]
    
    return [user, password]


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def read_data_file(ifile):

    with open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    return data

#-------------------------------------------------------------------------------

if __name__ == '__main__':

    try:
        part = sys.argv[1]
        part.strip()
    except:
        print(" USAGE: copy_data_from_occ_part.py <part>")
        exit(1)

#
#--- check whether a blob extraction is currently running_<part>; if so, stop
#
    ifile   = house_keeping + 'running_' + part
    try:
        running = read_data_file(ifile)
        if running[0] == '1':
            exit(1)
        else:
            write_run_file('1', part)
    except:
        write_run_file('0', part)
        exit(1)

    try:
        copy_data_from_occ_part(part)
    except:
        pass

    write_run_file('0', part)
