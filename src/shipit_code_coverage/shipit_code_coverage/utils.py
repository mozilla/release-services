import time


def wait_until(operation, timeout=30):
    elapsed = 0
    while elapsed < timeout:
        ret = operation()
        if ret is not None:
            return ret
        time.sleep(60)
        elapsed += 1

    return None
