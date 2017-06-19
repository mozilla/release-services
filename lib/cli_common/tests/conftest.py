import pytest
import logbook


@pytest.fixture(scope='module')
def logger():
    """
    Build a logger
    """

    import cli_common.log

    cli_common.log.init_logger('cli_common', level=logbook.DEBUG)
    return cli_common.log.get_logger(__name__)
