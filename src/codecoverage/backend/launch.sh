#!/bin/sh

python /bin/codecoverage_backend_worker &
python /bin/codecoverage_backend_worker &
gunicorn codecoverage_backend.flask:app --log-file -
