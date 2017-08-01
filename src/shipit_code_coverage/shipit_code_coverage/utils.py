# -*- coding: utf-8 -*-
import time
from concurrent.futures import ThreadPoolExecutor


def wait_until(operation, timeout=30):
    elapsed = 0
    while elapsed < timeout:
        ret = operation()
        if ret:
            return ret
        time.sleep(60)
        elapsed += 1

    return None


class ThreadPoolExecutorResult(ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        self.futures = []
        super(ThreadPoolExecutorResult, self).__init__(*args, **kwargs)

    def submit(self, *args, **kwargs):
        future = super(ThreadPoolExecutorResult, self).submit(*args, **kwargs)
        self.futures.append(future)
        return future

    def __exit__(self, *args):
        for future in self.futures:
            future.result()
        return super(ThreadPoolExecutorResult, self).__exit__(*args)
