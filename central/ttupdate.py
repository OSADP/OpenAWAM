#!/usr/bin/python
# ttupdate.py: Query database for recent observations and write new
# traveltimes table. 
#
# Still to do: Exit without doing anything if another instance of this script
# is running. This will allow us to call the script by database trigger
# whenever a record is written to the messages table, without fear of
# filling memory/conflicting updates.
#
# Also should move all constants e.g. TIMEDELTA to a table in the database
# to avoid having to modify packaged scripts for site customization.

from sqlalchemy import *
from sqlalchemy.sql import func
import dbinit
import datetime
import time
import sys

# Amount of time to look back for matches
TIMEDELTA = datetime.timedelta (minutes=15)

# timestamps are in UTC, so get current time and date in UTC
now_utc = datetime.datetime.utcnow ()

oldest_datestamp = now_utc - TIMEDELTA

engine = dbinit.engine
session = dbinit.session
Links = dbinit.Links
Nodes = dbinit.Nodes
Messages = dbinit.Messages
Traveltimes = dbinit.Traveltimes

def get_speed_from_tt (tt_sec, linklen, metric=False):
    # Given a travel time and link length, return the speed in mph if metric
    # is False, or in kph if metric is True.
    # Link length must be in meters if metric is set to True.
    # Link length must be in feet if metric is set to False.

    tt_hrs = tt_sec / 3600.0
    if metric:
        numerator = linklen / 1000.0
    else:
        numerator = linklen / 5280.0
    return numerator / tt_hrs

# Empty the target table (traveltimes)
session.query (Traveltimes).delete()
session.commit ()

# Iterate over all links in the database
for link in session.query (Links):
    linkdesc = link.name+" "+link.direction
    linklen  = link.length
    start    = link.start_id
    end      = link.end_id
    linkgid  = link.gid
    
    # Query for all records newer than the oldest allowed datestamp, which
    # have id equal to start_id
    startid_msgs = session.query (Messages).filter (Messages.dateandtime > oldest_datestamp).filter(Messages.loc_id==start)
    
    # Query for all records newer than the oldest allowed datestamp, which
    # have id equal to end_id
    endid_msgs = session.query (Messages).filter (Messages.dateandtime > oldest_datestamp).filter(Messages.loc_id==end)

    matches_for_this_link = {}
    
    # Look for matching addresses where timestamp for observation at end is
    # greater than timestamp for observation at start
    for msg in startid_msgs:
        thisaddr = msg.address
        thistime = msg.dateandtime
        for other_msg in endid_msgs:
            if other_msg.address != thisaddr:
                continue
            if other_msg.dateandtime <= thistime:
                continue
            # Found a match. If the address is not already in the matches
            # dictionary, add it. If in dictionary, keep whichever has the
            # shortest travel time on the theory that this is the better
            # representation of travel time between links
            tt = other_msg.dateandtime - thistime
            tt_sec = tt.total_seconds ()
            mph = get_speed_from_tt (tt_sec, linklen)
            if thisaddr in matches_for_this_link:
                oldmph = matches_for_this_link [thisaddr]
                if oldmph < mph:
                    matches_for_this_link [thisaddr] = (mph, tt_sec)
            else:
                matches_for_this_link [thisaddr] = (mph, tt_sec)
    numobs     = 0
    accum_mph  = 0
    accum_tt   = 0
    for addr, linkdata in matches_for_this_link.iteritems ():
        print linkdesc, addr, "%7.2f mph %7.2f sec" % linkdata
        numobs += 1
        accum_mph += linkdata [0]
        accum_tt  += linkdata [1]

    if numobs > 0:
        avgmph = accum_mph / numobs
        avgtt  = accum_tt  / numobs
        print "Link summary:", linkdesc, "%7.2f mph %7.2f sec" % (avgmph, avgtt)
        newttlink = Traveltimes (
                        link_id    = linkgid,
                        traveltime = avgtt,
                        speed      = avgmph
                                  )
        session.add (newttlink)
        session.commit ()

