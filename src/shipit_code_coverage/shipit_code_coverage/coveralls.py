import requests


def upload(data):
    r = requests.post('https://coveralls.io/api/v1/jobs', files={
        'json_file': data
    })

    try:
        print(r.json())
    except ValueError:
        raise Exception('Failure to submit data. Response [%s]: %s' % (r.status_code, r.text))  # NOQA
