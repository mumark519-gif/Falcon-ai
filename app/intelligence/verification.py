from __future__ import annotations
from typing import Any
class VerificationEngine:
    def verify(self,expected:Any,actual:Any)->dict[str,Any]:
        ok=actual is not None and (expected is None or actual==expected or str(expected).lower() in str(actual).lower())
        return {"verified":ok,"expected":expected,"actual":actual}
