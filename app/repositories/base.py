from __future__ import annotations
from typing import Generic,TypeVar
T=TypeVar("T")
class Repository(Generic[T]):
    def __init__(self):self.items={}
    def get(self,key):return self.items.get(key)
    def save(self,key,value):self.items[key]=value;return value
    def delete(self,key):return self.items.pop(key,None)
