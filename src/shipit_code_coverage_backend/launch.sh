#!/bin/sh

python /bin/shipit_code_coverage_backend_worker &
python /bin/shipit_code_coverage_backend_worker &
gunicorn shipit_code_coverage_backend.flask:app --log-file -
