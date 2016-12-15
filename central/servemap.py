#!/usr/bin/python
# servemap.py: Send geojson data to a map instance via websockets.
# 
# putting this here temporarily:
# how to check number of messages for a given location ID
# SELECT COUNT ("loc_id") FROM "public"."messages" WHERE ("loc_id" = 4);
#

"""
This script initializes a WebSocket web page server and accepts connections
from computers wishing to display the travel-time map.

It then idles in the background, waiting to be triggered by the database
(or the database travel-time update script, haven't decided which yet).
When activated, it reads the database travel-time table and sends a join
of the traveltimes table with the links table. (Only those links with travel
times will be mapped.)

This script must be run in python3 because the websockets module requires it.
The version of sqlalchemy that works with python3 is installed via the
python3-sqlalchemy package.
geoalchemy2 is compatible with python3. Install using:
    sudo easy_install3 geoalchemy2
The python3 interface to postgresql is installed via:
    sudo apt-get install python3-psycopg2
    
"""

from sqlalchemy import *
from sqlalchemy.sql import func
import dbparams
import datetime
import time

# Amount of time to look back for matches
TIMEDELTA = datetime.timedelta (minutes=15)

# Travel time matrix, stores observations about travel times
class tt:
    def __init__ (self):
        self.aleseb = {'tt':1,'numobs':0}
        self.aleswb = {'tt':1,'numobs':0}
        self.cacteb = {'tt':1,'numobs':0}
        self.cactwb = {'tt':1,'numobs':0}
        self.elswnb = {'tt':1,'numobs':0}
        self.elswsb = {'tt':1,'numobs':0}
        self.frednb = {'tt':1,'numobs':0}
        self.fredsb = {'tt':1,'numobs':0}

    def __repr__ (self):
        # Travel time is reported in miles per hour
        fmt = "%2.2f MPH"
        to_return = ""
        if self.aleseb ['numobs'] > 0:
            mystr = fmt % (1800.0/self.aleseb ['tt'])
            to_return  += "Alessandro EB: " + mystr + ' numobs '+str(self.aleseb ['numobs']) + '\n'
        if self.aleswb  ['numobs'] > 0:
            mystr = fmt % (1800.0/self.aleswb ['tt'])
            to_return += "Alessandro WB: " + mystr + ' numobs '+str(self.aleswb ['numobs']) + '\n'
        if self.cacteb ['numobs'] > 0:
            mystr = fmt % (1800.0/self.cacteb ['tt'])
            to_return += "Cactus EB:     " + mystr + ' numobs '+str(self.cacteb ['numobs']) + '\n'
        if self.cactwb  ['numobs'] > 0:
            mystr = fmt % (1800.0/self.cactwb ['tt'])
            to_return += "Cactus WB:     " + mystr + ' numobs '+str(self.cactwb ['numobs']) + '\n'
        if self.elswnb ['numobs'] > 0:
            mystr = fmt % (1800.0/self.elswnb ['tt'])
            to_return += "Elsworth NB:   " + mystr + ' numobs '+str(self.elswnb ['numobs']) + '\n'
        if self.elswsb ['numobs'] > 0:
            mystr = fmt % (1800.0/self.elswsb ['tt'])
            to_return += "Elsworth SB:   " + mystr + ' numobs '+str(self.elswsb ['numobs']) + '\n'
        if self.frednb ['numobs'] > 0:
            mystr = fmt % (1800.0/self.frednb ['tt'])
            to_return += "Frederick NB:  " + mystr + ' numobs '+str(self.frednb ['numobs']) + '\n'
        if self.fredsb ['numobs'] > 0:
            mystr = fmt % (1800.0/self.fredsb ['tt'])
            to_return += "Frederick SB:  " + mystr + ' numobs '+str(self.fredsb ['numobs']) + '\n'
        return to_return

    def update_tt (self, link, ts1, ts2):
        # Given the name of a link and two timestamps, calculate the
        # travel time and increment the number of observations
        working_with = getattr (self, link)
        ttdiff = ts2 - ts1
        ttdiff_sec = ttdiff.total_seconds ()
        num_prev_obs = working_with ["numobs"]
        num_obs = num_prev_obs + 1
        if num_prev_obs == 0:
            working_with ["tt"] = ttdiff_sec
        else:
            old_tt = working_with ["tt"]
            old_tt_weighted = old_tt * num_prev_obs
            working_with ["tt"] = (old_tt_weighted + ttdiff_sec) / num_obs
        working_with ["numobs"] = num_obs
        setattr (self, link, working_with)

    def calc_tt (self, obs1, obs2):
        # Given two observations of the same ID, figure out if it
        # corresponds to a link and if so, enter the travel time
        # obs1 and obs2 must be dictionaries with the following
        # entries:
        #   hostname: string (represents the location)
        #   timestamp: datetime object
        #   (no need to have address here because calling function
        #   is supposed to take care of that)

        if obs1 ['hostname'] != obs2 ['hostname']:
            # obsa will always be the earlier timestamp
            assert obs1 ['timestamp'] != obs2 ['timestamp']
            if obs1 ['timestamp'] > obs2 ['timestamp']: 
                obsa = obs2
                obsb = obs1
            else:
                obsa = obs1
                obsb = obs2
            hostnma = obsa ['hostname']
            hostnmb = obsb ['hostname']
            timestampa = obsa ['timestamp']
            timestampb = obsb ['timestamp']
            if hostnma == 'elsw-cact' and hostnmb == 'fred-cact':
                self.update_tt ('cacteb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'elsw-ales' and hostnmb == 'fred-ales':
                self.update_tt ('aleseb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'fred-cact' and hostnmb == 'elsw-cact':
                self.update_tt ('cactwb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'fred-ales' and hostnmb == 'elsw-ales':
                self.update_tt ('aleswb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'elsw-ales' and hostnmb == 'elsw-cact':
                self.update_tt ('elswsb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'elsw-cact' and hostnmb == 'elsw-ales':
                self.update_tt ('elswnb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'fred-cact' and hostnmb == 'fred-ales':
                self.update_tt ('frednb',obsa ['timestamp'],obsb ['timestamp'])
            elif hostnma == 'fred-ales' and hostnmb == 'fred-cact':
                self.update_tt ('fredsb',obsa ['timestamp'],obsb ['timestamp'])
        else:
            print "Dupe"

while True:

    obs = {}

    engine = dbparams.engine
    metadata = dbparams.metadata
    messages = dbparams.messages
    conn = engine.connect()

    current_time = datetime.datetime.now ()
    earliest_time = current_time - TIMEDELTA

    # query for recent observations (since current time - TIMEDELTA)
    # Although query selects only records which have duplicate ID's,
    # duplicates are not guaranteed due to post-evaluation of the
    # timestamp

    # s generates a list of recently observed (anonymized) addresses.
    s = select ([messages]).where(messages.c.dateandtime > earliest_time)

    alias1 = s.alias ()
    alias2 = s.alias ()

    t = select ([alias1,alias2]).where(alias1.c.address == alias2.c.address).where(alias1.c.location != alias2.c.location)
    #result1 = conn.execute (s)
    result2 = conn.execute (t)

    # Here above, in result2, we have a list of recently observed addresses which
    # were observed at different locations, with timestamps. We will need to improve
    # the query later, but for now we have two sets of timestamps for one address
    # in each row.

    obs = {}

    #print result2.rowcount
    for row in result2:
        loc1 = row [1]
        loc2 = row [5]
        addr1 = row [3]
        addr2 = row [7]
        time1 = row [2]
        time2 = row [6]
        assert addr1 == addr2
        if addr1 in obs:
            # For now, passing. Later, we may need to include this one anyway
            pass
        else:
            obs [addr1] = {}
            obs [addr1][1] = {}
            obs [addr1][2] = {}
            obs [addr1][1]['hostname'] = loc1
            obs [addr1][2]['hostname'] = loc2
            obs [addr1][1]['timestamp'] = time1
            obs [addr1][2]['timestamp'] = time2

    #print obs

    tts = tt ()

    for someaddr, observations in obs.iteritems ():
        tts.calc_tt (observations[1],observations[2])

    print datetime.datetime.now()
    print tts

    time.sleep (30)
