#!/usr/bin/python

# init_db.py: Call create_all
#

import dbinit

engine = dbinit.engine
Base = dbinit.Base

Base.metadata.create_all(engine)





