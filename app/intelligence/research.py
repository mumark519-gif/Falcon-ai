from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import hashlib
@dataclass
class Source:
    url: str
    title: str = ""
    snippet: str = ""
    credibility: float = 0.5
    claims: list[str] = field(default_factory=list)
@dataclass
class ResearchReport:
    query: str
    sources: list[Source]
    claims: list[dict[str,Any]]
    contradictions: list[dict[str,Any]]
    citations: list[str]
class ResearchController:
    def deduplicate(self,sources:list[Source])->list[Source]:
        seen=set(); out=[]
        for s in sources:
            key=hashlib.sha256(s.url.split("?")[0].encode()).hexdigest()
            if key not in seen: seen.add(key); out.append(s)
        return out
    def rank(self,sources:list[Source])->list[Source]:
        return sorted(sources,key=lambda s:(s.credibility,len(s.snippet)),reverse=True)
    def report(self,query:str,sources:list[Source],claims:list[dict[str,Any]]|None=None)->ResearchReport:
        src=self.rank(self.deduplicate(sources)); claims=claims or []
        contradictions=[]
        for i,a in enumerate(claims):
            for b in claims[i+1:]:
                if a.get("topic") == b.get("topic") and a.get("value") != b.get("value"):
                    contradictions.append({"a":a,"b":b})
        return ResearchReport(query,src,claims,contradictions,[s.url for s in src])
