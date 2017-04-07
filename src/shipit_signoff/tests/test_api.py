import json
import jsonschema
from os import path
import yaml

import shipit_signoff

def test_swagger_spec():
    here = path.abspath(path.dirname(__file__))
    shipit_lib = path.abspath(path.dirname(shipit_signoff.__file__))
    swagger_schema = json.loads(open(path.join(here, "swagger-2.0-spec.json")).read())
    swagger_file = yaml.load(open(path.join(shipit_lib, "api.yml")).read())

    # Raises if invalid
    jsonschema.validate(swagger_file, swagger_schema)
