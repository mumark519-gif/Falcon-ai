from __future__ import annotations
ROLE_PERMISSIONS={"admin":{"*"},"developer":{"chat","read","code","github_read","github_write"},"analyst":{"chat","read","research","documents"},"user":{"chat","read","documents"}}
def allowed(role:str,permission:str)->bool:
    return permission in ROLE_PERMISSIONS.get(role,set()) or "*" in ROLE_PERMISSIONS.get(role,set())
