#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH="$PYTHONPATH:$DIR"
export FLASK_APP=shipit_dashboard
export DATABASE_URL=sqlite:///$DIR/shipit.db
