from __future__ import annotations
import time,uuid
from contextlib import contextmanager
@contextmanager
def span(name:str,**attrs):
    started=time.time(); trace_id=str(uuid.uuid4())
    try: yield {"trace_id":trace_id,"name":name,"attributes":attrs}
    finally: _=time.time()-started
