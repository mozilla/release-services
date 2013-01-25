#!/usr/bin/env python
import os
import site

wsgidir = os.path.dirname(__file__)

# Add our vendor lib dir to the path
site.addsitedir(os.path.abspath(os.path.join(wsgidir, 'vendor/lib/python')))

import mapper.app
mapper.app.mapfile_dir = os.path.join(wsgidir, "mapfiles")
application = mapper.app.app
