# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from os import path

import jsonschema
import yaml

HERE = path.abspath(path.dirname(__file__))
SIGNOFF_DIR = path.join(HERE, '..', 'shipit_signoff')


def test_swagger_spec():
    with open(path.join(HERE, 'swagger-2.0-spec.json')) as f:
        swagger_schema = json.load(f)

    with open(path.join(SIGNOFF_DIR, 'api.yml')) as f:
        swagger_file = yaml.load(f.read())

    jsonschema.validate(swagger_file, swagger_schema)
