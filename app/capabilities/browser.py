from __future__ import annotations
class BrowserCapability:
    def open(self,url:str): 
        import requests
        r=requests.get(url,timeout=30,allow_redirects=True)
        return {"url":r.url,"status_code":r.status_code,"text":r.text,"headers":dict(r.headers)}
