# -*- coding: utf-8 -*-

from shipit_code_coverage import utils
import time


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
    assert not utils.retry(do_raise, wait_between_retries=0)

    i = {}

    def try_twice():
        if 'tried' in i:
            return
        else:
            i['tried'] = True
            raise Exception('Please try again.')

    assert utils.retry(try_twice, wait_between_retries=0)


def test_threadpoolexecutorresult():
    with utils.ThreadPoolExecutorResult() as executor:
        executor.submit(lambda: True)
        executor.submit(lambda: False)

    # Test that ThreadPoolExecutorResult throws an exception when one of the tasks fails.
    try:
        with utils.ThreadPoolExecutorResult() as executor:
            executor.submit(lambda: True)
            executor.submit(do_raise)
        assert False
    except:
        assert True

    # Tast that ThreadPoolExecutorResult's context returns as soon as a task fails.
    try:
        now = time.time()
        with utils.ThreadPoolExecutorResult() as executor:
            executor.submit(lambda: time.sleep(5))
            executor.submit(do_raise)
        assert False
    except:
        assert time.time() - now < 2

    # Test that futures that were not scheduled yet are cancelled.
    try:
        with utils.ThreadPoolExecutorResult(max_workers=1) as executor:
            f1 = executor.submit(lambda: time.sleep(1))
            f2 = executor.submit(do_raise)
            executor.submit(lambda: time.sleep(1))
            f4 = executor.submit(lambda: time.sleep(1))
            f5 = executor.submit(lambda: time.sleep(1))
            f6 = executor.submit(lambda: time.sleep(1))
        assert False
    except:
        assert f1.done() and not f1.cancelled()
        assert f2.exception() is not None
        # Not enough time to cancel the third future, scheduled right after the one which raises an exception.
        # When we try to cancel it, it's already running, so the cancellation fails.
        assert f4.cancelled()
        assert f5.cancelled()
        assert f6.cancelled()
