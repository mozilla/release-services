#!/bin/sh

python /bin/code_coverage_backend_worker &
python /bin/code_coverage_backend_worker &
gunicorn code_coverage_backend.flask:app --log-file -
