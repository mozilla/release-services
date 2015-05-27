# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import tempfile

from cStringIO import StringIO
from relengapi import cmd


_settings = {}


def run_main(args, settings={'SQLALCHEMY_DATABASE_URIS': {}}):
    global _settings
    _settings = settings

    fd, filename = tempfile.mkstemp()
    with os.fdopen(fd, "wt") as f:
        f.write("from relengapi.lib.testing.subcommands import _settings\n")
        f.write("globals().update(_settings)\n")
    os.environ['RELENGAPI_SETTINGS'] = filename

    old_out = sys.stdout
    sys.stdout = fake_stdout = StringIO()
    try:
        cmd.main(args)
    except SystemExit:
        pass
    finally:
        old_out.write(sys.stdout.getvalue())
        sys.stdout = old_out
        os.unlink(filename)
        del os.environ['RELENGAPI_SETTINGS']
    return fake_stdout.getvalue()
