#!/bin/sh

if ps -ef | grep -v grep | grep "/data/mta4/Script/SOH/copy_data_from_occ.py snap" ; then
    exit 0
else
    /data/mta4/Script/SOH/copy_data_from_occ.py snap
    exit 0
fi

