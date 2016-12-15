#!/bin/bash
# reload_shps: Run the following programs to reinitialize the database:
#
# dbinit.py to create the tables
# shp2pgsql to import shapefiles into the clean tables

# Start with empty link, node, and message tables
# How can we drop the tables in this script first?

# Run this only from the directory where the script resides, I don't feel like
# taking the extra effort to make this universal
./dbinit.py
shp2pgsql -a -s 2230 shp/nodes.shp | psql -d openawam
shp2pgsql -a -s 2230 shp/links.shp | psql -d openawam

