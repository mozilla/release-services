# -*- coding: utf-8 -*-

import time

import pytest

import cli_common.utils


def do_raise():
    raise Exception('Err')


def test_retry():
    assert cli_common.utils.retry(lambda: True) is True
    assert cli_common.utils.retry(lambda: False) is False
    with pytest.raises(Exception):
        cli_common.utils.retry(do_raise, wait_between_retries=0)

    i = {}

    def try_twice():
        if 'tried' in i:
            return
        else:
            i['tried'] = True
            raise Exception('Please try again.')

    assert cli_common.utils.retry(try_twice, wait_between_retries=0) is None


def test_threadpoolexecutorresult():
    with cli_common.utils.ThreadPoolExecutorResult() as executor:
        executor.submit(lambda: True)
        executor.submit(lambda: False)

    # Test that ThreadPoolExecutorResult throws an exception when one of the tasks fails.
    with pytest.raises(Exception):
        with cli_common.utils.ThreadPoolExecutorResult() as executor:
            executor.submit(lambda: True)
            executor.submit(do_raise)

    # Tast that ThreadPoolExecutorResult's context returns as soon as a task fails.
    with pytest.raises(Exception):
        now = time.time()
        with cli_common.utils.ThreadPoolExecutorResult() as executor:
            executor.submit(lambda: time.sleep(5))
            executor.submit(do_raise)

    assert time.time() - now < 2

    # Test that futures that were not scheduled yet are cancelled.
    with pytest.raises(Exception):
        with cli_common.utils.ThreadPoolExecutorResult(max_workers=1) as executor:
            f1 = executor.submit(lambda: time.sleep(1))
            f2 = executor.submit(do_raise)
            executor.submit(lambda: time.sleep(1))
            f4 = executor.submit(lambda: time.sleep(1))
            f5 = executor.submit(lambda: time.sleep(1))
            f6 = executor.submit(lambda: time.sleep(1))

    assert f1.done() and not f1.cancelled()
    assert f2.exception() is not None
    # Not enough time to cancel the third future, scheduled right after the one which raises an exception.
    # When we try to cancel it, it's already running, so the cancellation fails.
    assert f4.cancelled()
    assert f5.cancelled()
    assert f6.cancelled()
