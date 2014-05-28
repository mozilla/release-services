#! /bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -e
cd "$( dirname "${BASH_SOURCE[0]}" )"
source ./validate-common.sh

status "running pep8 -- slaveloan"
pep8 --config=pep8rc relengapi || not_ok "pep8 failed"

status "running pylint"
pylint relengapi --rcfile=pylintrc || not_ok "pylint failed"

show_results

