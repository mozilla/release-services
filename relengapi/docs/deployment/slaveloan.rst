Slaveloan
=========

Bugzilla
........

Slaveloan makes extensive use of Bugzilla's REST API for classifying new loans, reopening slave tracking bugs, etc.

In order to use it, you *must* specify where and what user to use (in the settings file). e.g.::

    BUGZILLA_URL = "https://bugzilla-dev.allizom.org/rest/"
    BUGZILLA_USER = "my.user@example.com"
    BUGZILLA_PASS = "my.passw0rd"

Slavealloc
..........

Slaveloan also makes use of ``slavealloc``'s API.

::

    SLAVEALLOC_URL = "http://slavealloc.pvt.build.mozilla.org/api"

SlaveAPI
..........

Slaveloan also makes use of SlaveAPI for a variety of tasks.

::

    SLAVEAPI_URL = "http://slaveapi-dev1.build.mozilla.org:8080/slaves/"
