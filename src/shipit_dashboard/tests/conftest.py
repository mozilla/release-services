import pytest
from shipit_dashboard import app
from releng_common import mocks


@pytest.yield_fixture(scope='module')
def client():
    """
    A Flask test client for shipit_dashboard
    with mockups enabled
    """
    with app.test_client() as client:
        with mocks.apply_mockups():
            yield client
