# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from releng_tooltool.flask import app


if __name__ == "__main__":
    app.run(**app.run_options())
