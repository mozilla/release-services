import json
import jsonschema
from os import path
import yaml


HERE = path.abspath(path.dirname(__file__))


def test_swagger_spec():
    import shipit_signoff

    shipit_dir = path.abspath(path.dirname(shipit_signoff.__file__))

    with open(path.join(HERE, "swagger-2.0-spec.json")) as f:
        swagger_schema = json.load(f)

    with open(path.join(shipit_dir, "api.yml")) as f:
        swagger_file = yaml.load(f.read())

    jsonschema.validate(swagger_file, swagger_schema)
