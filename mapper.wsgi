#!/Users/asasaki/wrk/virtualenv/mh/bin/python
import os
import site

wsgidir = os.path.dirname(__file__)

# Add our vendor lib dir to the path
# TODO fix
site.addsitedir('/Users/asasaki/wrk/virtualenv/mh/lib/python2.7/site-packages')

import mapper.app
application = mapper.app.app
