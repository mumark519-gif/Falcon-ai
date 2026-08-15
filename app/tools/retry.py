from __future__ import annotations
import time
def retry(fn,retries=3,backoff=.5):
    last=None
    for i in range(retries):
        try:return fn()
        except Exception as e:last=e;time.sleep(backoff*(2**i))
    raise last
