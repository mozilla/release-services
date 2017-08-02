# -*- coding: utf-8 -*-

from shipit_code_coverage import utils


def do_raise():
    raise Exception('Err')


def test_wait_until():
    assert utils.wait_until(lambda: False, 1, 1) is None
    assert utils.wait_until(lambda: None, 1, 1) is None
    assert utils.wait_until(lambda: '', 1, 1) is None
    assert utils.wait_until(lambda: True, 1, 1) is not None
    assert utils.wait_until(lambda: 'Prova', 1, 1) is not None

    i = {}

    def try_twice():
        if 'tried' in i:
            return True
        else:
            i['tried'] = True
            return False

    assert utils.wait_until(try_twice, 2, 1) is not None


def test_retry():
    assert utils.retry(lambda: True)
    assert utils.retry(lambda: False)
    assert not utils.retry(do_raise)

    i = {}

    def try_twice():
        if 'tried' in i:
            return
        else:
            i['tried'] = True
            raise Exception('Please try again.')

    assert utils.retry(try_twice)


def test_threadpoolexecutorresult():
    with utils.ThreadPoolExecutorResult() as executor:
        executor.submit(lambda: True)
        executor.submit(lambda: False)

    try:
        with utils.ThreadPoolExecutorResult() as executor:
            executor.submit(lambda: True)
            executor.submit(do_raise)
        assert False
    except:
        assert True
