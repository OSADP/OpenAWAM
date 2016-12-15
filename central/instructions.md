# OpenAWAM Central Software

The central software component of OpenAWAM is responsible for storing
observations and generating maps and reports. It consists of the following
modules:

- **Database.** Currently only PostgreSQL is supported because use of the
  "geoalchemy2" package was selected for abstracting the GIS database, and
  that package only supports PostgreSQL. However, PostgreSQL is a powerful,
  readily available open-source database. Together with PostGIS (a PostgreSQL
  extension), a highly capable open-source GIS database is available for
  use by OpenAWAM. To the author's knowledge, there is no limit to the number
  of field nodes that can be supported, and address records stored in the
  database are only limited by the server's capabilities (CPU and disk space
  being the relevant limiting factors).
- **Message receiver.** *(write_data.py)* This script is responsible for
  listening for messages from field nodes and writing them to the database
  as soon as they are received.
- **Map server.** This script queries the database at regular intervals to
  update the travel-time model based on the most recent address observations,
  and serves a map to any connected Web browser. *WebSockets* is used to 
  maintain an open connection between the browser and the server. The result
  is a map that is continuously updated whenever new travel-time estimates
  are available, without the need to refresh the Web browser.
- **Query tool.** *(in progress)* When completed, this module will allow
  the user to query historical data to, for example, perform origin/
  destination analyses.

Note to potential users: Documentation is in progress, will be complete prior
to need. In other words, if you start deploying field nodes, I will finish
the documentation before you need to do the central component.

=====================================
Installation
=====================================

**Dependencies**
The following packages are needed to run the central component of OpenAWAM:

- sqlalchemy
- geoalchemy2
- postgis (will install postgresql)

**Setting up the database (IN PROGRESS)**
(To do: Test what is the minimum needed to do to get the write_data.py script
to run--e.g. PostGIS configuration, include the table with the projections--
how was that created?)

(The last step in this section needs to be successfully running write_data.py
so that the database is ready to accept the shapefile import in the next step)

In postgresql.conf, comment out timezone = 'localtime' replace with timezone = 'UTC'

**Setting up the map**
(Talk about the two shapefiles to create, and how to import using shp2pgsql)

(Consider putting an empty set of shapefiles in the repository for use in
getting started)

How to select a coordinate system

Once you've selected a coordinate system, make note of the WKID or SRID, which
is a number that defines the map projection assumed in your shapefile. You'll
need to provide this to the GIS database when you import the shapefiles.

If you've previously imported data into the database, you need to clear the
table before re-importing the data using shp2pgsql. (Come up with a command
line program to do this for the user)

Run:
  shp2pgsql -a -s 2230 nodes.shp | psql -d openawam


links--one for each direction. If curvilinear, draw along the curve.
Let ArcGIS calculate the length

===============================
Usage
===============================

(Open the html file on the local machine)
  
==============================
CONTACT US
==============================

OpenAWAM is currently being developed by:

John Kerenyi
City of Moreno Valley
(951) 413-3199

Kali Fogel
Los Angeles County Metropolitan Transportation Authority
(213) 922-2665

Additional contact information can be found on the project's homepage:
https://github.com/OSADP/OpenAWAM
