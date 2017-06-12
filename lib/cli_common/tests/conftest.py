import pytest
import logbook
from cli_common.log import init_logger


@pytest.fixture(scope='module')
def logger():
    """
    Build a logger
    """
    return init_logger(level=logbook.DEBUG)
