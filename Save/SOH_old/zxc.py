#!/usr/bin/env /proj/sot/ska/bin/python

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

start = 662687994
stop  = 662774394
out   = maude.get_msids('AOGBIAS1', start, stop)
val   = str((list(out['data'][0]['values']))[-1])
print("I AM HERE: " + str(val))
