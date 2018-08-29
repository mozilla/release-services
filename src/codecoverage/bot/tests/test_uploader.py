# -*- coding: utf-8 -*-

import pytest
import requests
import responses

from shipit_code_coverage import uploader


@responses.activate
def test_get_codecov(mock_secrets, codecov_commits):
    data = uploader.get_codecov('0548f006a32c138218ad586177db83486c82a09e')
    assert data['commit']['state'] == 'complete'

    with pytest.raises(requests.exceptions.HTTPError):
        uploader.get_codecov('7d7b21f5ede24dbdd59e17980a332f4b240f8e13')
