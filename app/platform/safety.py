from __future__ import annotations
WRITE_PREFIXES=("create","update","delete","send","publish","commit","push","execute")
def requires_confirmation(action:str)->bool:
    s=action.strip().lower()
    return any(s.startswith(x) for x in WRITE_PREFIXES)
def redact_secrets(value):
    if isinstance(value,dict): return {k: ("[REDACTED]" if any(x in k.lower() for x in ("token","secret","password","api_key")) else redact_secrets(v)) for k,v in value.items()}
    if isinstance(value,list): return [redact_secrets(x) for x in value]
    return value
