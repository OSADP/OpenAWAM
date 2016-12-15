#!/usr/bin/python

# write_data.py: Listen for packets from OpenAWAM nodes, write data to 
# database.
#
# This script relies on sqlalchemy to abstract the database. PostgreSQL is
# currently the underlying database. This is easily changed using the
# ENGINE_STRING constant. Note that sqlite does not allow concurrent
# reading and writing, so if you attempt to use that engine you will
# experience frequent crashes.
#
# Install sqlalchemy using "apt install python-sqlalchemy"

import sys
from sqlalchemy import *
import dbinit
import socket
import datetime

# This constant triggers a warning message to stdout, which is redirected
# to syslog by default (check systemd service write_data.service to confirm
# or change) if the timestamp on the received data is more than this many
# seconds off from the current time and date
MAX_TIMEDIFF_IN_SEC = 5

ZERO = datetime.timedelta (0)

# UTC timezone class
class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()


def convert_syslog_datetime (datetimestr):
    # Given a string in the high-resolution format written by rsyslog (which
    # is an isoformat), generate and return a timezone-aware datetime.datetime
    # object.
    #
    # There are some modules which will do this conversion, but I don't want
    # to add another dependency and I don't want to test timezone
    # compatibility.
    #
    # All datetimes are stored in the database as UTC with zero offset.
    
    dtonly = datetimestr [:-6]
    tzonly = datetimestr [-6:]
    
    tzsign  = tzonly [0]
    tzhours = int (tzonly [1:3])
    tzmins  = int (tzonly [4:6])
    
    utctimedelta_abs = datetime.timedelta(hours=tzhours,minutes=tzmins)
    if tzsign == "-":
        utctimedelta = -utctimedelta_abs
    else:
        assert tzsign == "+" # tzsign must be + or -
        utctimedelta = utctimedelta_abs
    
    # This effort to explicitly use UTC turns out to be unnecessary because
    # PostgreSQL just applies the timezone in its configuration, but since
    # that may change in the future, I'm leaving it in. It also helps make
    # clear to readers that the intent is for timezones to be stored as UTC.
    observed_datetime = datetime.datetime.strptime (dtonly, '%Y-%m-%dT%H:%M:%S.%f')
    utcdt = observed_datetime - utctimedelta
    utcdt_aware = datetime.datetime (utcdt.year,
                                     utcdt.month,
                                     utcdt.day,
                                     utcdt.hour,
                                     utcdt.minute,
                                     utcdt.second,
                                     utcdt.microsecond,
                                     utc)
    
    return utcdt_aware

def syslog_listener ():
    # Based on pysyslog2db which was written by, and placed into the public
    # domain by, Laode Hadi Cahyadi.
    # Returns a dictionary as follows:
    
    # location--string, actually just the field node's hostname as reported
    # by rsyslog on the field node
    # address--the anonymized MAC of the observation
    # dateandtime--datetime.datetime object with the time and date of
    # the observation as reported by the field node
    
    # Assumes syslog is using UDP to transmit data--may wish to re-visit
    # (e.g. what happens if two nodes transmit data at the same instant?)
    
    HOST = ''         # Symbolic name meaning all available interfaces
    PORT = 50101 
    BUFFER_SIZE = 8192
    
    to_return = {}
    
    valid_msg = False
    while not valid_msg:
    
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.bind ((HOST, PORT))
        msg, addr = s.recvfrom (BUFFER_SIZE)
        #print addr, msg
        if 'bluelog' in msg and 'INVALID_MAC' not in msg and "Shutdown OK" not in msg and "Init OK" not in msg:
            valid_msg = True

    mainmsg = msg.split ('>')[-1]
    mainmsg_parts = mainmsg.split (' ')
    datetime_str=mainmsg_parts [0]
    location = unicode (mainmsg_parts [1])
    address = mainmsg_parts [-1]
    
    dateandtime = convert_syslog_datetime (datetime_str)
    
    to_return ['address'] = address
    to_return ['dateandtime'] = dateandtime

    # Get location ID from location
    # Come back to this: Is there an automatic way to select the proper
    # foreign key when creating the record?
    lid_record = session.query (dbinit.Nodes).filter (dbinit.Nodes.location==location).first ()
    lid = lid_record.gid
    to_return ['loc_id'] = lid

    return to_return

engine = dbinit.engine
session = dbinit.session

print "write_data.py starting."
# Ensure message is written out right away
sys.stdout.flush ()

# Listen for messages and write to database as they are received
while True:
    msg = syslog_listener ()
    print msg
    newmessage = dbinit.Messages (
            loc_id      = msg ['loc_id'],
            dateandtime = msg ['dateandtime'],
            address     = msg ['address']
                                  )
    session.add (newmessage)
    session.commit ()

