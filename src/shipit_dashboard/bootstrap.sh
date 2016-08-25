#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RELENG_DIR="$( dirname $DIR)/releng_common"

export DEBUG=true
export PYTHONPATH="$PYTHONPATH:$DIR:$RELENG_DIR"
export FLASK_APP=shipit_dashboard
export DATABASE_URL=sqlite:///$DIR/shipit.db
