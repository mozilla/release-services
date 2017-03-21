def test_logger(logger):
    # TODO capture stdout
    logger.info('Test')
    logger.info('Test args', arg1='aaa')
    assert True
