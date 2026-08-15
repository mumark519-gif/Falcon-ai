# Backend Growth Plan

The current backend can keep running from `app/main.py`. As Falcon AI expands, split features into route modules and services:

1. Move auth routes into `app/api/routes/auth.py`.
2. Move profile/user routes into `app/api/routes/users.py`.
3. Move analysis routes into `app/api/routes/analysis.py`.
4. Move JWT settings from `app/auth.py` into `app/core/settings.py`.
5. Move database operations into `app/repositories`.
