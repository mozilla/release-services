#!/bin/sh

python /bin/shipit_uplift_worker &
python /bin/shipit_uplift_worker &
gunicorn shipit_uplift.flask:app --log-file -
