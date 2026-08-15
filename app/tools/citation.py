from __future__ import annotations
from dataclasses import dataclass
@dataclass
class Citation:
    url:str
    title:str=''
    source_type:str='web'
    confidence:float=.5
def normalize_citations(items):
    seen=set();out=[]
    for x in items:
        if x.url not in seen:seen.add(x.url);out.append(x)
    return out
