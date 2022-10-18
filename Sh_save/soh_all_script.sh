#!/bin/sh
if ps -ef | grep -v grep | grep "/data/mta4/Script/SOH/copy_data_from_occ.py all"; then
    exit 0
else

    /data/mta4/Script/SOH/copy_data_from_occ.py all
    exit 0
fi

