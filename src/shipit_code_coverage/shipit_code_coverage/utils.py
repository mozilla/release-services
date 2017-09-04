# -*- coding: utf-8 -*-
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


def wait_until(operation, timeout=30, interval=60):
    elapsed = 0
    while elapsed < timeout:
        ret = operation()
        if ret:
            return ret
        time.sleep(interval)
        elapsed += 1

    return None


def retry(operation, retries=3):
    successful = False
    while not successful and retries > 0:
        try:
            operation()
            successful = True
        except:
            retries -= 1
    return successful


class ThreadPoolExecutorResult(ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        self.futures = []
        super(ThreadPoolExecutorResult, self).__init__(*args, **kwargs)

    def submit(self, *args, **kwargs):
        future = super(ThreadPoolExecutorResult, self).submit(*args, **kwargs)
        self.futures.append(future)
        return future

    def __exit__(self, *args):
        for future in concurrent.futures.as_completed(self.futures):
            future.result()
        return super(ThreadPoolExecutorResult, self).__exit__(*args)
