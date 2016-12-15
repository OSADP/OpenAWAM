#!/usr/bin/python

# dbinit.py: Configuration of database parameters.
#

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, relationship, backref
from geoalchemy2 import Geometry

DBUSER = 'john'
DBPASS = 'koahmc'
DBHOST = 'localhost'
DBNAME = 'openawam'

ENGINE_STRING = 'postgresql://'+DBUSER+':'+DBPASS+'@'+DBHOST+'/'+DBNAME

engine = create_engine (ENGINE_STRING)
Session = sessionmaker (bind=engine)
session = Session ()
Base = declarative_base ()

# For future reference--a primary key is only generated if we define it
# here. According to the SQLAlchemy book, a primary key is also mandatory
class Messages (Base):
    __tablename__ = 'messages'
    id = Column (Integer, primary_key=True)
    loc_id = Column (Integer, ForeignKey ('nodes.gid'))
    dateandtime = Column (DateTime (timezone=True), nullable=False)
    address = Column (String (16), nullable=False)

class Links (Base):
    __tablename__ = 'links'
    gid = Column (Integer, primary_key=True)
    name = Column (Unicode, nullable=False) # Street name
    direction = Column (Unicode) # example: EB, NB
    # start is an entry in the Nodes table for the node at the start of the
    # link
    start_id = Column (Integer, ForeignKey ('nodes.gid'), nullable=False)
    # end is an entry in the Nodes table for the node at the end of the link
    end_id = Column (Integer, ForeignKey ('nodes.gid'), nullable=False)
    # srid=2230 is NAD83 California zone (same as many shapefiles created
    # by MoVal's GIS group)
    geom = Column (Geometry ('MULTILINESTRING', srid=2230), nullable=False)
    # The length of the link is calculated when the table is created
    # or modified. The geometry of the road network is not expected to change
    # very often, so having a static length should not be an issue.
    # Being able to read the length from the database instead of
    # calculating it every time we need it should reduce CPU usage.
    # The units on length are defined elsewhere (come back to this--
    # can we get it from the locale? Does it even matter since the
    # ultimate output is speed and we can work out the units on speed
    # separately from the units on length?)
    length = Column (Float)
    
class Nodes (Base):
    __tablename__ = 'nodes'
    gid = Column (Integer, primary_key=True)
    # location is populated from a shapefile used to generate this table.
    # It must match the hostname of the field node at the location.
    location = Column (Unicode, nullable=False)
    geom = Column (Geometry ('POINT', srid=2230), nullable=False)

class Traveltimes (Base):
    __tablename__ = 'traveltimes'
    id = Column (Integer, primary_key=True)
    link_id = Column (Integer, ForeignKey ('links.gid'))
    traveltime = Column (Float)
    speed = Column (Float)
